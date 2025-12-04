from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)

class EmergencyAgent(BaseAgent):
    """Emergency triage and coordination agent"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "emergency_triage")
        
        self.critical_keywords = [
            'chest pain', 'heart attack', 'stroke', 'can\'t breathe',
            'suicide', 'bleeding heavily', 'unconscious', 'seizure',
            'severe headache', 'overdose', 'poison'
        ]
        
        # Subscribe to all patient conversations
        # Will be set up after message bus is initialized
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process emergency situation"""
        self.set_status("processing")
        
        try:
            patient_id = input_data["patient_id"]
            message = input_data["message"]
            context = input_data.get("context", {})
            
            logger.critical(f"🚨 EMERGENCY ALERT for patient {patient_id}")
            
            # Step 1: Assess emergency level
            emergency_level = self._assess_emergency_level(message)
            
            # Step 2: Coordinate emergency response (parallel)
            logger.info(f"🚑 Coordinating emergency response...")
            
            results = await asyncio.gather(
                self._notify_doctors(patient_id, message, emergency_level),
                self._grant_emergency_access(patient_id),
                self._find_nearest_hospital(context.get("location")),
                self._alert_emergency_contact(patient_id),
                return_exceptions=True
            )
            
            doctor_notification, access_grant, nearest_hospital, emergency_contact_alert = results
            
            # Step 3: Broadcast emergency status
            await self.broadcast(
                "EMERGENCY_IN_PROGRESS",
                {
                    "patient_id": patient_id,
                    "level": emergency_level,
                    "status": "coordinated"
                },
                priority=1
            )
            
            self.set_status("idle")
            
            return {
                "emergency_level": emergency_level,
                "doctors_notified": doctor_notification,
                "access_granted": access_grant,
                "nearest_hospital": nearest_hospital,
                "emergency_contact_alerted": emergency_contact_alert,
                "instructions": self._get_emergency_instructions(emergency_level)
            }
            
        except Exception as e:
            logger.error(f"❌ Emergency Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle emergency alerts"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "EMERGENCY_ALERT":
            return await self.process(payload)
        elif msg_type == "MONITOR_CONVERSATION":
            # Monitor for emergency keywords
            if self._contains_emergency_keywords(payload.get("message", "")):
                logger.warning(f"⚠️ Emergency keywords detected")
                return await self.process(payload)
        
        return None
    
    def _assess_emergency_level(self, message: str) -> str:
        """Assess emergency severity"""
        message_lower = message.lower()
        
        life_threatening = ['heart attack', 'stroke', 'unconscious', 'not breathing', 'suicide']
        severe = ['chest pain', 'bleeding heavily', 'seizure', 'severe pain']
        
        if any(keyword in message_lower for keyword in life_threatening):
            return "life_threatening"
        elif any(keyword in message_lower for keyword in severe):
            return "severe"
        else:
            return "moderate"
    
    async def _notify_doctors(self, patient_id: str, message: str, level: str) -> Dict:
        """Notify nearby doctors"""
        logger.info(f"📞 Notifying doctors for {level} emergency")
        
        # Send to Doctor Notification Agent
        result = await self.send_message(
            "doc-1",
            "EMERGENCY_DOCTOR_NEEDED",
            {
                "patient_id": patient_id,
                "emergency_level": level,
                "symptoms": message
            },
            priority=1
        )
        
        return {"notified": True, "doctors_contacted": 3}  # Mock data
    
    async def _grant_emergency_access(self, patient_id: str) -> Dict:
        """Grant emergency access to medical records"""
        logger.info(f"🔓 Granting emergency access to records")
        
        # Request from Records Agent
        result = await self.send_message(
            "rec-1",
            "GRANT_EMERGENCY_ACCESS",
            {"patient_id": patient_id},
            priority=1
        )
        
        # Also trigger blockchain agent
        await self.send_message(
            "chain-1",
            "LOG_EMERGENCY_ACCESS",
            {"patient_id": patient_id, "reason": "emergency_protocol"},
            priority=1
        )
        
        return {"access_granted": True}
    
    async def _find_nearest_hospital(self, location: Optional[str]) -> Dict:
        """Find nearest hospital with emergency services"""
        logger.info(f"🏥 Finding nearest hospital")
        
        # Mock implementation - would integrate with Google Maps API
        return {
            "hospital_name": "Apollo Hospital Emergency",
            "distance_km": 2.3,
            "phone": "102",
            "estimated_time": "8 minutes"
        }
    
    async def _alert_emergency_contact(self, patient_id: str) -> Dict:
        """Alert patient's emergency contact"""
        logger.info(f"👨‍👩‍👧 Alerting emergency contact")
        
        # Would integrate with SMS/WhatsApp API
        return {
            "contact_alerted": True,
            "contact_name": "Family Member",
            "method": "SMS"
        }
    
    def _contains_emergency_keywords(self, message: str) -> bool:
        """Check if message contains emergency keywords"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.critical_keywords)
    
    def _get_emergency_instructions(self, level: str) -> str:
        """Get emergency instructions for patient"""
        if level == "life_threatening":
            return "🚨 CALL 102/108 IMMEDIATELY. Do not wait. Emergency services have been notified."
        elif level == "severe":
            return "⚠️ This requires urgent medical attention. Please go to the nearest emergency room. Help is being coordinated."
        else:
            return "Please seek medical attention soon. We are coordinating with healthcare providers."
