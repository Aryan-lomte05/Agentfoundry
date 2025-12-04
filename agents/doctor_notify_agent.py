from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)

class DoctorNotifyAgent(BaseAgent):
    """Doctor notification and coordination agent"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "doctor_coordination")
        
        # Mock doctor database
        self.available_doctors = {
            "cardiology": [
                {"id": "doc-001", "name": "Dr. Sharma", "distance_km": 2.3, "available": True},
                {"id": "doc-002", "name": "Dr. Patel", "distance_km": 4.1, "available": True}
            ],
            "general": [
                {"id": "doc-003", "name": "Dr. Kumar", "distance_km": 1.5, "available": True},
                {"id": "doc-004", "name": "Dr. Singh", "distance_km": 3.2, "available": False}
            ],
            "emergency": [
                {"id": "doc-005", "name": "Dr. Emergency", "distance_km": 0.8, "available": True}
            ]
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify and coordinate with doctors"""
        self.set_status("processing")
        
        try:
            action = input_data.get("action", "find_doctors")
            patient_id = input_data["patient_id"]
            
            if action == "find_doctors":
                specialty = input_data.get("specialty", "general")
                location = input_data.get("location")
                
                doctors = await self._find_nearby_doctors(specialty, location)
                return {"doctors": doctors}
            
            elif action == "notify_doctors":
                doctor_ids = input_data.get("doctor_ids", [])
                message = input_data.get("message", "")
                
                results = await self._notify_doctors(doctor_ids, patient_id, message)
                return {"notifications_sent": len(results), "results": results}
            
            elif action == "emergency_notification":
                emergency_level = input_data.get("emergency_level", "moderate")
                symptoms = input_data.get("symptoms", "")
                
                result = await self._emergency_notify(patient_id, emergency_level, symptoms)
                return result
            
            self.set_status("idle")
            
        except Exception as e:
            logger.error(f"❌ Doctor Notify Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle doctor notification requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "EMERGENCY_DOCTOR_NEEDED":
            logger.warning(f"🚨 Emergency doctor notification")
            return await self.process({**payload, "action": "emergency_notification"})
        
        elif msg_type == "FIND_SPECIALISTS":
            return await self.process({**payload, "action": "find_doctors"})
        
        elif msg_type == "NOTIFY_DOCTOR":
            return await self.process({**payload, "action": "notify_doctors"})
        
        return None
    
    async def _find_nearby_doctors(self, specialty: str, location: Optional[Dict]) -> List[Dict]:
        """Find nearby available doctors"""
        logger.info(f"🔍 Finding {specialty} doctors")
        
        # Get doctors from database
        doctors = self.available_doctors.get(specialty, self.available_doctors["general"])
        
        # Filter available
        available = [d for d in doctors if d['available']]
        
        # Sort by distance
        available.sort(key=lambda x: x['distance_km'])
        
        return available[:5]  # Return top 5
    
    async def _notify_doctors(self, doctor_ids: List[str], patient_id: str, message: str) -> List[Dict]:
        """Send notifications to specific doctors"""
        logger.info(f"📞 Notifying {len(doctor_ids)} doctors")
        
        results = []
        
        for doctor_id in doctor_ids:
            # In production: Send SMS/Email/WhatsApp
            # For demo: Mock notification
            
            notification_result = {
                "doctor_id": doctor_id,
                "status": "sent",
                "method": "SMS",
                "timestamp": "now"
            }
            
            results.append(notification_result)
            
            # Simulate async notification
            await asyncio.sleep(0.1)
        
        return results
    
    async def _emergency_notify(self, patient_id: str, level: str, symptoms: str) -> Dict:
        """Emergency notification to all nearby doctors"""
        logger.critical(f"🚨 EMERGENCY NOTIFICATION: {level}")
        
        # Get emergency doctors
        emergency_docs = self.available_doctors["emergency"]
        general_docs = [d for d in self.available_doctors["general"] if d['available']]
        
        all_doctors = emergency_docs + general_docs[:3]  # Emergency + 3 general
        
        # Send notifications in parallel
        notification_tasks = [
            self._send_emergency_sms(doc['id'], patient_id, level, symptoms)
            for doc in all_doctors
        ]
        
        results = await asyncio.gather(*notification_tasks)
        
        # Request emergency access to records
        await self.send_message(
            "rec-1",
            "GRANT_EMERGENCY_ACCESS",
            {"patient_id": patient_id},
            priority=1
        )
        
        return {
            "emergency_notification": True,
            "doctors_notified": len(all_doctors),
            "notifications": results,
            "nearest_doctor": all_doctors[0] if all_doctors else None
        }
    
    async def _send_emergency_sms(self, doctor_id: str, patient_id: str, level: str, symptoms: str) -> Dict:
        """Send emergency SMS to doctor"""
        # In production: Integrate with Twilio/AWS SNS
        
        sms_content = f"""🚨 EMERGENCY ALERT
        
Patient ID: {patient_id}
Level: {level.upper()}
Symptoms: {symptoms}

Please respond immediately or forward to on-call doctor.

Reply ACCEPT to handle case.
"""
        
        logger.info(f"📱 SMS sent to {doctor_id}")
        
        return {
            "doctor_id": doctor_id,
            "method": "SMS",
            "status": "delivered",
            "content_preview": sms_content[:50]
        }
