from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from database.models import MedicalRecord
from database.database import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)

class RecordsAgent(BaseAgent):
    """Medical records management agent"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "medical_records")
        self.access_log = []
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage medical records operations"""
        self.set_status("processing")
        
        try:
            operation = input_data.get("operation", "retrieve")
            patient_id = input_data["patient_id"]
            
            if operation == "retrieve":
                records = await self._retrieve_records(patient_id, input_data.get("requester_id"))
                return {"records": records}
            
            elif operation == "store":
                record_data = input_data["record_data"]
                result = await self._store_record(patient_id, record_data)
                return result
            
            elif operation == "grant_access":
                doctor_id = input_data["doctor_id"]
                duration = input_data.get("duration", 24)  # hours
                result = await self._grant_access(patient_id, doctor_id, duration)
                return result
            
            elif operation == "revoke_access":
                doctor_id = input_data["doctor_id"]
                result = await self._revoke_access(patient_id, doctor_id)
                return result
            
            self.set_status("idle")
            
        except Exception as e:
            logger.error(f"❌ Records Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle records requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "RETRIEVE_RECORDS":
            return await self.process({**payload, "operation": "retrieve"})
        
        elif msg_type == "STORE_RECORD":
            return await self.process({**payload, "operation": "store"})
        
        elif msg_type == "GRANT_EMERGENCY_ACCESS":
            logger.warning(f"🚨 Emergency access granted for {payload['patient_id']}")
            # Emergency bypass - grant immediate access
            result = await self._emergency_access_grant(payload['patient_id'])
            
            # Log to blockchain
            await self.send_message(
                "chain-1",
                "LOG_EMERGENCY_ACCESS",
                payload,
                priority=1
            )
            
            return result
        
        return None
    
    async def _retrieve_records(self, patient_id: str, requester_id: Optional[str]) -> Dict:
        """Retrieve patient medical records"""
        logger.info(f"📂 Retrieving records for patient {patient_id}")
        
        # Check access permissions
        if requester_id and not await self._check_access_permission(patient_id, requester_id):
            logger.warning(f"⛔ Access denied for {requester_id}")
            return {"error": "Access denied", "records": []}
        
        # Retrieve from database
        db = next(get_db())
        records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
        
        # Log access
        self.access_log.append({
            "patient_id": patient_id,
            "requester_id": requester_id,
            "timestamp": "now",
            "action": "retrieve"
        })
        
        return {
            "records": [self._record_to_dict(r) for r in records],
            "count": len(records)
        }
    
    async def _store_record(self, patient_id: str, record_data: Dict) -> Dict:
        """Store new medical record"""
        logger.info(f"💾 Storing record for patient {patient_id}")
        
        db = next(get_db())
        
        new_record = MedicalRecord(
            patient_id=patient_id,
            record_type=record_data.get("type", "consultation"),
            content=record_data.get("content", ""),
            diagnosis=record_data.get("diagnosis"),
            medications=record_data.get("medications", []),
            metadata=record_data.get("metadata", {})
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        # Notify blockchain agent to create NFT
        await self.send_message(
            "chain-1",
            "CREATE_RECORD_NFT",
            {
                "patient_id": patient_id,
                "record_id": new_record.id,
                "record_hash": self._hash_record(new_record)
            },
            priority=3
        )
        
        return {
            "success": True,
            "record_id": new_record.id
        }
    
    async def _grant_access(self, patient_id: str, doctor_id: str, duration_hours: int) -> Dict:
        """Grant access to doctor for specified duration"""
        logger.info(f"🔓 Granting access: Patient {patient_id} → Doctor {doctor_id} for {duration_hours}h")
        
        # This would integrate with blockchain smart contract
        # For now, store in local cache/database
        
        # Notify blockchain agent
        await self.send_message(
            "chain-1",
            "GRANT_ACCESS_ON_CHAIN",
            {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "duration": duration_hours * 3600  # Convert to seconds
            },
            priority=2
        )
        
        return {
            "success": True,
            "expires_in_hours": duration_hours
        }
    
    async def _revoke_access(self, patient_id: str, doctor_id: str) -> Dict:
        """Revoke doctor access"""
        logger.info(f"🔒 Revoking access: Patient {patient_id} → Doctor {doctor_id}")
        
        await self.send_message(
            "chain-1",
            "REVOKE_ACCESS_ON_CHAIN",
            {"patient_id": patient_id, "doctor_id": doctor_id},
            priority=3
        )
        
        return {"success": True}
    
    async def _emergency_access_grant(self, patient_id: str) -> Dict:
        """Grant emergency access (bypass normal permissions)"""
        logger.critical(f"🚨 EMERGENCY ACCESS GRANTED for {patient_id}")
        
        # Grant to all nearby doctors (in real system)
        # For demo: Grant universal temporary access
        
        return {
            "emergency_access": True,
            "expires_in_hours": 24,
            "access_level": "full"
        }
    
    async def _check_access_permission(self, patient_id: str, requester_id: str) -> bool:
        """Check if requester has permission to access records"""
        # In production, check blockchain smart contract
        # For demo: Allow all access (or implement simple DB check)
        return True
    
    def _record_to_dict(self, record) -> Dict:
        """Convert SQLAlchemy record to dict"""
        return {
            "id": record.id,
            "date": record.created_at.isoformat() if hasattr(record, 'created_at') else None,
            "type": record.record_type,
            "diagnosis": record.diagnosis,
            "medications": record.medications
        }
    
    def _hash_record(self, record) -> str:
        """Generate hash of record for blockchain"""
        import hashlib
        import json
        
        record_str = json.dumps({
            "id": record.id,
            "patient_id": record.patient_id,
            "content": record.content
        }, sort_keys=True)
        
        return hashlib.sha256(record_str.encode()).hexdigest()
