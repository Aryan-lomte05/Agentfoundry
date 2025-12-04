from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from models.inference import generate_response
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TreatmentAgent(BaseAgent):
    """Treatment planning and medication recommendation agent"""
    
    def __init__(self, agent_id: str, name: str, model, tokenizer):
        super().__init__(agent_id, name, "treatment_planning")
        self.model = model
        self.tokenizer = tokenizer
        
        # Drug interaction database (simplified)
        self.drug_interactions = {
            "aspirin": ["warfarin", "ibuprofen"],
            "metformin": ["alcohol"],
            "lisinopril": ["potassium supplements"]
        }
        
        # Indian essential medicines
        self.indian_essential_meds = {
            "fever": ["paracetamol", "ibuprofen"],
            "infection": ["amoxicillin", "azithromycin"],
            "diabetes": ["metformin", "glimepiride"],
            "hypertension": ["amlodipine", "atenolol"],
            "malaria": ["artemether-lumefantrine"],
            "tuberculosis": ["rifampicin", "isoniazid", "pyrazinamide", "ethambutol"]
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate treatment plan"""
        self.set_status("processing")
        
        try:
            diagnostic_data = input_data.get("diagnostic_data", {})
            patient_id = input_data["patient_id"]
            current_medications = input_data.get("current_medications", [])
            allergies = input_data.get("allergies", [])
            
            logger.info(f"💊 Creating treatment plan for patient {patient_id}")
            
            # Extract diagnosis
            likely_conditions = diagnostic_data.get("likely_conditions", [])
            severity = diagnostic_data.get("severity", "mild")
            
            # Generate medication recommendations
            medications = self._recommend_medications(likely_conditions, severity, allergies)
            
            # Check drug interactions
            interaction_warnings = self._check_interactions(medications, current_medications)
            
            # Generate treatment plan using model
            treatment_prompt = self._build_treatment_prompt(
                diagnostic_data, medications, interaction_warnings
            )
            detailed_plan = await generate_response(
                self.model, self.tokenizer, treatment_prompt, max_tokens=400
            )
            
            # Lifestyle recommendations
            lifestyle = self._get_lifestyle_recommendations(likely_conditions)
            
            result = {
                "medications": medications,
                "interaction_warnings": interaction_warnings,
                "detailed_plan": detailed_plan,
                "lifestyle_recommendations": lifestyle,
                "follow_up_days": self._determine_followup(severity),
                "red_flags": self._identify_red_flags(diagnostic_data)
            }
            
            # Notify Medication Agent to start tracking
            await self.send_message(
                "med-1",
                "START_MEDICATION_TRACKING",
                {
                    "patient_id": patient_id,
                    "medications": medications
                },
                priority=3
            )
            
            # Reward patient with tokens for following plan
            await self.send_message(
                "chain-1",
                "REWARD_TREATMENT_PLAN_CREATED",
                {"patient_id": patient_id, "amount": 10},
                priority=4
            )
            
            self.set_status("idle")
            return result
            
        except Exception as e:
            logger.error(f"❌ Treatment Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle treatment planning requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "DIAGNOSTIC_COMPLETE":
            return await self.process(payload)
        elif msg_type == "UPDATE_TREATMENT_PLAN":
            logger.info(f"🔄 Updating treatment plan")
            return await self.process(payload)
        
        return None
    
    def _recommend_medications(self, conditions: List[Dict], severity: str, allergies: List[str]) -> List[Dict]:
        """Recommend medications based on diagnosis"""
        medications = []
        
        for condition in conditions[:2]:  # Top 2 conditions
            condition_name = condition.get("condition", "")
            
            if condition_name in self.indian_essential_meds:
                drugs = self.indian_essential_meds[condition_name]
                
                for drug in drugs[:2]:  # Max 2 drugs per condition
                    if drug.lower() not in [a.lower() for a in allergies]:
                        medications.append({
                            "name": drug.title(),
                            "dosage": self._get_standard_dosage(drug),
                            "frequency": "As prescribed",
                            "duration": self._get_duration(condition_name, severity),
                            "instructions": self._get_instructions(drug)
                        })
        
        # Add symptomatic treatment
        if severity in ["moderate", "severe"]:
            medications.append({
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "Every 6 hours if needed",
                "duration": "3-5 days",
                "instructions": "Take with food"
            })
        
        return medications
    
    def _check_interactions(self, new_meds: List[Dict], current_meds: List[str]) -> List[str]:
        """Check for drug interactions"""
        warnings = []
        
        for new_med in new_meds:
            new_med_name = new_med['name'].lower()
            
            if new_med_name in self.drug_interactions:
                interacting_drugs = self.drug_interactions[new_med_name]
                
                for current_med in current_meds:
                    if current_med.lower() in interacting_drugs:
                        warnings.append(
                            f"⚠️ {new_med['name']} may interact with {current_med}. Consult doctor before taking together."
                        )
        
        return warnings
    
    def _get_standard_dosage(self, drug: str) -> str:
        """Get standard dosage for common drugs"""
        dosages = {
            "paracetamol": "500mg",
            "ibuprofen": "400mg",
            "amoxicillin": "500mg",
            "azithromycin": "500mg",
            "metformin": "500mg",
            "amlodipine": "5mg"
        }
        return dosages.get(drug.lower(), "As prescribed")
    
    def _get_duration(self, condition: str, severity: str) -> str:
        """Determine treatment duration"""
        if condition == "tuberculosis":
            return "6 months (AKT-4 regimen)"
        elif severity == "severe":
            return "7-10 days"
        elif severity == "moderate":
            return "5-7 days"
        else:
            return "3-5 days"
    
    def _get_instructions(self, drug: str) -> str:
        """Get administration instructions"""
        instructions = {
            "paracetamol": "Take with water after food",
            "amoxicillin": "Take on empty stomach, 1 hour before meals",
            "metformin": "Take with meals to reduce stomach upset",
            "amlodipine": "Take at the same time each day"
        }
        return instructions.get(drug.lower(), "Follow doctor's instructions")
    
    def _get_lifestyle_recommendations(self, conditions: List[Dict]) -> List[str]:
        """Get lifestyle recommendations"""
        recommendations = [
            "Drink plenty of water (8-10 glasses daily)",
            "Get adequate rest (7-8 hours sleep)",
            "Maintain good hygiene practices"
        ]
        
        for condition in conditions:
            condition_name = condition.get("condition", "")
            
            if condition_name == "diabetes":
                recommendations.extend([
                    "Monitor blood sugar regularly",
                    "Avoid sugar and refined carbs",
                    "Exercise for 30 minutes daily"
                ])
            elif condition_name == "hypertension":
                recommendations.extend([
                    "Reduce salt intake",
                    "Avoid stress",
                    "Regular BP monitoring"
                ])
            elif condition_name in ["malaria", "dengue"]:
                recommendations.extend([
                    "Use mosquito nets",
                    "Keep surroundings clean",
                    "Avoid water stagnation"
                ])
        
        return recommendations[:6]  # Max 6 recommendations
    
    def _determine_followup(self, severity: str) -> int:
        """Determine follow-up days"""
        if severity == "critical":
            return 1
        elif severity == "severe":
            return 3
        elif severity == "moderate":
            return 7
        else:
            return 14
    
    def _identify_red_flags(self, diagnostic_data: Dict) -> List[str]:
        """Identify warning signs to watch for"""
        severity = diagnostic_data.get("severity", "mild")
        symptoms = diagnostic_data.get("symptoms", [])
        
        red_flags = []
        
        if severity in ["severe", "critical"]:
            red_flags.append("Seek immediate medical attention if symptoms worsen")
        
        if "fever" in symptoms:
            red_flags.append("If fever persists beyond 3 days or rises above 103°F, consult doctor immediately")
        
        if "cough" in symptoms:
            red_flags.append("If you cough up blood or have severe breathing difficulty, go to ER")
        
        red_flags.append("If you experience any severe side effects from medications, stop and contact doctor")
        
        return red_flags
    
    def _build_treatment_prompt(self, diagnostic_data: Dict, medications: List, warnings: List) -> str:
        """Build prompt for detailed treatment plan"""
        conditions = ", ".join([c['condition'] for c in diagnostic_data.get('likely_conditions', [])])
        meds_str = ", ".join([m['name'] for m in medications])
        
        prompt = f"""<s>[INST] You are an expert treatment planning AI for Indian healthcare.

Diagnosis: {conditions}
Severity: {diagnostic_data.get('severity', 'mild')}
Recommended Medications: {meds_str}

Create a comprehensive, easy-to-understand treatment plan in Hindi and English. Include:
1. How to take medications properly
2. What to expect during recovery
3. When to see a doctor
4. Lifestyle modifications

Keep language simple for rural patients. [/INST]"""
        
        return prompt
