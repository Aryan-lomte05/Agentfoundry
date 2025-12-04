from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from PIL import Image
import torch
from torchvision import transforms
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ImagingAgent(BaseAgent):
    """Medical image analysis agent (X-ray, CT scans)"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "medical_imaging")
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    async def load_imaging_model(self):
        """Load medical imaging model (e.g., BiomedCLIP or ResNet)"""
        try:
            # For hackathon: Use pre-trained ResNet for classification
            # In production: Use BiomedCLIP or specialized medical model
            from torchvision.models import resnet50, ResNet50_Weights
            self.model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
            self.model.eval()
            logger.info("✅ Imaging model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load imaging model: {e}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze medical image"""
        self.set_status("processing")
        
        try:
            image_path = input_data["image_path"]
            image_type = input_data.get("image_type", "xray")
            patient_id = input_data["patient_id"]
            
            logger.info(f"🔬 Analyzing {image_type} for patient {patient_id}")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0)
            
            # Analyze image
            if self.model is None:
                await self.load_imaging_model()
            
            with torch.no_grad():
                features = self.model(image_tensor)
            
            # Classification (simplified for hackathon)
            classification = self._classify_xray(features, image_type)
            
            # Generate detailed report
            report = self._generate_report(classification, image_type)
            
            result = {
                "classification": classification,
                "report": report,
                "confidence": classification.get("confidence", 0.0),
                "abnormalities_detected": classification.get("abnormal", False),
                "recommendations": self._get_recommendations(classification)
            }
            
            # Send results back to Diagnostic Agent
            await self.send_message(
                "diag-1",
                "IMAGING_RESULTS",
                result,
                priority=2
            )
            
            self.set_status("idle")
            return result
            
        except Exception as e:
            logger.error(f"❌ Imaging Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle imaging requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "ANALYZE_IMAGE":
            return await self.process(payload)
        elif msg_type == "IMAGING_REQUIRED":
            logger.info(f"📸 Imaging requested for patient")
            return {"status": "waiting_for_upload"}
        
        return None
    
    def _classify_xray(self, features: torch.Tensor, image_type: str) -> Dict[str, Any]:
        """Classify X-ray image (simplified)"""
        # For hackathon: Simple rule-based classification
        # In production: Use specialized medical imaging model
        
        # Mock classification based on feature statistics
        feature_mean = features.mean().item()
        feature_std = features.std().item()
        
        if image_type == "chest_xray":
            if feature_mean > 0.5:
                return {
                    "finding": "Possible pneumonia",
                    "confidence": 0.72,
                    "abnormal": True,
                    "details": "Consolidation pattern observed in right lung field"
                }
            elif feature_mean > 0.3:
                return {
                    "finding": "Possible pleural effusion",
                    "confidence": 0.65,
                    "abnormal": True,
                    "details": "Blunting of costophrenic angle noted"
                }
            else:
                return {
                    "finding": "No obvious abnormality",
                    "confidence": 0.85,
                    "abnormal": False,
                    "details": "Lung fields appear clear"
                }
        
        return {
            "finding": "Analysis complete",
            "confidence": 0.5,
            "abnormal": False
        }
    
    def _generate_report(self, classification: Dict, image_type: str) -> str:
        """Generate detailed radiology report"""
        finding = classification.get("finding", "")
        details = classification.get("details", "")
        confidence = classification.get("confidence", 0.0)
        
        report = f"""RADIOLOGY REPORT
        
Image Type: {image_type.replace('_', ' ').title()}

FINDINGS:
{finding}

DETAILS:
{details}

AI CONFIDENCE: {confidence*100:.1f}%

IMPRESSION:
{'Abnormality detected. Recommend clinical correlation and possible follow-up imaging.' if classification.get('abnormal') else 'No significant abnormality detected on initial AI analysis.'}

NOTE: This is an AI-assisted preliminary analysis. Final interpretation should be made by a qualified radiologist.
"""
        return report
    
    def _get_recommendations(self, classification: Dict) -> list:
        """Get follow-up recommendations"""
        if classification.get("abnormal"):
            return [
                "Consult with a radiologist for confirmation",
                "Clinical correlation recommended",
                "Consider follow-up imaging in 2-4 weeks",
                "Evaluate for antibiotic therapy if pneumonia suspected"
            ]
        else:
            return [
                "No immediate follow-up required",
                "Continue monitoring symptoms",
                "Repeat imaging if symptoms worsen"
            ]
