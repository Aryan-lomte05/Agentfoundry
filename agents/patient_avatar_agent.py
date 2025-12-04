from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from models.inference import generate_response, generate_streaming_response
from rag.retrieval import retrieve_patient_context
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PatientAvatarAgent(BaseAgent):
    """Primary patient-facing agent - coordinates all interactions"""
    
    def __init__(self, agent_id: str, name: str, model, tokenizer):
        super().__init__(agent_id, name, "patient_interface")
        self.model = model
        self.tokenizer = tokenizer
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process patient query and coordinate with other agents
        
        Args:
            input_data: {
                "message": str,
                "patient_id": str,
                "language": str,
                "conversation_history": List[Dict]
            }
        """
        self.set_status("processing")
        
        try:
            message = input_data["message"]
            patient_id = input_data["patient_id"]
            language = input_data.get("language", "en")
            
            # Step 1: Retrieve patient history context via RAG
            logger.info(f"🔍 Retrieving patient context for {patient_id}")
            patient_context = await retrieve_patient_context(patient_id, message)
            
            # Step 2: Check for emergency keywords
            is_emergency = await self._check_emergency(message)
            
            if is_emergency:
                # Send to Emergency Triage Agent immediately
                logger.warning(f"🚨 Emergency detected: {message[:50]}...")
                emergency_response = await self.send_message(
                    "emerg-1",
                    "EMERGENCY_ALERT",
                    {
                        "patient_id": patient_id,
                        "message": message,
                        "context": patient_context
                    },
                    priority=1  # CRITICAL
                )
                
                return {
                    "response": "🚨 I detect this may be an emergency. Help is being coordinated immediately. Please stay calm.",
                    "emergency": True,
                    "emergency_data": emergency_response
                }
            
            # Step 3: Send to Diagnostic Agent for analysis
            logger.info(f"🔬 Sending to Diagnostic Agent")
            diagnostic_result = await self.send_message(
                "diag-1",
                "ANALYZE_SYMPTOMS",
                {
                    "message": message,
                    "patient_id": patient_id,
                    "context": patient_context
                },
                priority=2
            )
            
            # Step 4: Generate response using fine-tuned model
            prompt = self._build_prompt(message, patient_context, diagnostic_result, language)
            response = await generate_response(self.model, self.tokenizer, prompt)
            
            # Step 5: Log interaction to blockchain
            await self.send_message(
                "chain-1",
                "LOG_INTERACTION",
                {
                    "patient_id": patient_id,
                    "query": message,
                    "response": response
                },
                priority=4
            )
            
            self.set_status("idle")
            
            return {
                "response": response,
                "diagnostic_data": diagnostic_result,
                "emergency": False,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"❌ Error in PatientAvatarAgent: {str(e)}")
            self.set_status("error")
            return {
                "response": "I apologize, but I encountered an error. Please try again or contact support if the issue persists.",
                "error": str(e)
            }
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle messages from other agents"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "DIAGNOSTIC_COMPLETE":
            logger.info(f"✅ Received diagnostic results")
            return payload
        elif msg_type == "TREATMENT_PLAN_READY":
            logger.info(f"💊 Received treatment plan")
            return payload
        
        return None
    
    async def _check_emergency(self, message: str) -> bool:
        """Check if message contains emergency keywords"""
        emergency_keywords = [
            'chest pain', 'can\'t breathe', 'can not breathe', 'cannot breathe',
            'suicide', 'kill myself', 'bleeding heavily', 'unconscious',
            'seizure', 'stroke', 'heart attack', 'severe headache',
            'सीने में दर्द', 'सांस नहीं आ रही', 'खून बह रहा है'  # Hindi
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in emergency_keywords)
    
    def _build_prompt(self, message: str, context: str, diagnostic: Any, language: str) -> str:
        """Build prompt for model with context"""
        lang_instruction = ""
        if language == "hi":
            lang_instruction = "Respond in Hindi (हिंदी में जवाब दें)."
        elif language == "ta":
            lang_instruction = "Respond in Tamil (தமிழில் பதிலளி)."
        
        prompt = f"""<s>[INST] You are a compassionate healthcare AI assistant for rural India.

Patient History:
{context}

Current Question: {message}

{lang_instruction}

Provide empathetic, medically accurate advice. If serious symptoms, advise seeing a doctor. [/INST]"""
        
        return prompt
