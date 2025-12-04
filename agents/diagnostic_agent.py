from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from models.inference import generate_response
from utils.logger import setup_logger
import re

logger = setup_logger(__name__)

class DiagnosticAgent(BaseAgent):
    """Specialized agent for medical diagnosis and symptom analysis"""
    
    def __init__(self, agent_id: str, name: str, model, tokenizer):
        super().__init__(agent_id, name, "diagnosis")
        self.model = model
        self.tokenizer = tokenizer
        
        # Disease patterns for India
        self.indian_disease_keywords = {
            'malaria': ['fever', 'chills', 'headache', 'sweating'],
            'dengue': ['high fever', 'body pain', 'rash', 'bleeding'],
            'tuberculosis': ['cough', 'weight loss', 'night sweats', 'blood in sputum'],
            'typhoid': ['sustained fever', 'weakness', 'stomach pain'],
            'diabetes': ['increased thirst', 'frequent urination', 'fatigue'],
            'hypertension': ['headache', 'dizziness', 'chest pressure']
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze symptoms and provide diagnostic insights"""
        self.set_status("processing")
        
        try:
            message = input_data["message"]
            patient_id = input_data["patient_id"]
            context = input_data.get("context", "")
            
            # Extract symptoms
            symptoms = self._extract_symptoms(message)
            
            # Calculate severity
            severity = self._assess_severity(symptoms, message)
            
            # Check for common Indian diseases
            likely_conditions = self._match_diseases(symptoms)
            
            # Check if imaging needed
            needs_imaging = self._check_imaging_requirement(symptoms, message)
            
            if needs_imaging:
                # Request imaging analysis
                logger.info(f"🏥 Requesting imaging analysis")
                await self.send_message(
                    "img-1",
                    "IMAGING_REQUIRED",
                    {"patient_id": patient_id, "symptoms": symptoms},
                    priority=2
                )
            
            # Generate detailed diagnostic analysis
            diagnostic_prompt = self._build_diagnostic_prompt(message, context, symptoms, likely_conditions)
            analysis = await generate_response(self.model, self.tokenizer, diagnostic_prompt, max_tokens=300)
            
            result = {
                "symptoms": symptoms,
                "severity": severity,
                "likely_conditions": likely_conditions,
                "analysis": analysis,
                "needs_imaging": needs_imaging,
                "recommended_tests": self._recommend_tests(symptoms)
            }
            
            # If moderate/severe, notify treatment agent
            if severity in ["moderate", "severe", "critical"]:
                await self.send_message(
                    "treat-1",
                    "DIAGNOSTIC_COMPLETE",
                    result,
                    priority=2
                )
            
            self.set_status("idle")
            return result
            
        except Exception as e:
            logger.error(f"❌ Diagnostic Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming messages"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "ANALYZE_SYMPTOMS":
            return await self.process(payload)
        elif msg_type == "IMAGING_RESULTS":
            logger.info(f"📊 Received imaging results, correlating with diagnosis")
            return payload
        
        return None
    
    def _extract_symptoms(self, message: str) -> list:
        """Extract symptoms from patient message"""
        # Simple keyword extraction (can be enhanced with NER)
        symptom_keywords = [
            'fever', 'cough', 'pain', 'headache', 'nausea', 'vomiting',
            'diarrhea', 'fatigue', 'weakness', 'rash', 'bleeding',
            'chest pain', 'shortness of breath', 'dizziness'
        ]
        
        message_lower = message.lower()
        found_symptoms = [s for s in symptom_keywords if s in message_lower]
        
        return found_symptoms
    
    def _assess_severity(self, symptoms: list, message: str) -> str:
        """Assess severity level"""
        critical_symptoms = ['chest pain', 'can\'t breathe', 'bleeding heavily', 'unconscious']
        severe_symptoms = ['high fever', 'severe pain', 'blood in', 'seizure']
        
        message_lower = message.lower()
        
        if any(s in message_lower for s in critical_symptoms):
            return "critical"
        elif any(s in message_lower for s in severe_symptoms) or len(symptoms) > 5:
            return "severe"
        elif len(symptoms) > 3:
            return "moderate"
        else:
            return "mild"
    
    def _match_diseases(self, symptoms: list) -> list:
        """Match symptoms to common Indian diseases"""
        matches = []
        
        for disease, disease_symptoms in self.indian_disease_keywords.items():
            overlap = len(set(symptoms) & set(disease_symptoms))
            if overlap >= 2:
                matches.append({
                    "condition": disease,
                    "match_score": overlap / len(disease_symptoms),
                    "confidence": "low" if overlap == 2 else "moderate" if overlap == 3 else "high"
                })
        
        return sorted(matches, key=lambda x: x['match_score'], reverse=True)[:3]
    
    def _check_imaging_requirement(self, symptoms: list, message: str) -> bool:
        """Determine if medical imaging is needed"""
        imaging_keywords = [
            'chest pain', 'breathing difficulty', 'cough with blood',
            'accident', 'injury', 'fracture', 'lung', 'chest'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in imaging_keywords)
    
    def _recommend_tests(self, symptoms: list) -> list:
        """Recommend lab tests based on symptoms"""
        test_recommendations = []
        
        if 'fever' in symptoms:
            test_recommendations.extend(['Complete Blood Count (CBC)', 'Malaria Test', 'Dengue NS1 Antigen'])
        if 'cough' in symptoms:
            test_recommendations.extend(['Chest X-ray', 'Sputum Test'])
        if 'fatigue' in symptoms or 'weakness' in symptoms:
            test_recommendations.extend(['Blood Sugar', 'Thyroid Function Test'])
        
        return list(set(test_recommendations))[:5]
    
    def _build_diagnostic_prompt(self, message: str, context: str, symptoms: list, conditions: list) -> str:
        """Build diagnostic prompt for model"""
        conditions_str = ", ".join([c['condition'] for c in conditions]) if conditions else "unclear"
        
        prompt = f"""<s>[INST] You are an expert diagnostic AI for Indian healthcare.

Patient History:
{context}

Current Symptoms: {', '.join(symptoms)}
Possible Conditions: {conditions_str}

Patient Query: {message}

Provide a detailed diagnostic analysis. Consider India-specific diseases like malaria, dengue, TB, typhoid. [/INST]"""
        
        return prompt
