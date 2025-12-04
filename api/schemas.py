from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Chat Schemas
class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    patient_id: str = Field(..., description="Patient ID")
    language: str = Field(default="en", description="Language code (en, hi, ta)")
    conversation_history: Optional[List[Dict]] = Field(default=None)

class ChatResponse(BaseModel):
    response: str
    diagnostic_data: Optional[Dict] = None
    emergency: bool = False
    language: str = "en"
    agent_logs: Optional[List[Dict]] = None

# Patient Schemas
class PatientCreate(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    location: Optional[Dict] = None

class PatientHistoryUpload(BaseModel):
    patient_id: str
    content: str
    record_type: str = "consultation"
    diagnosis: Optional[str] = None
    medications: Optional[List[str]] = None

# Blockchain Schemas
class AccessGrantRequest(BaseModel):
    patient_id: str
    doctor_id: str
    duration_hours: int = 24

class TokenRewardRequest(BaseModel):
    patient_id: str
    amount: int
    reason: str

# Medical Image Schemas
class ImageAnalysisRequest(BaseModel):
    patient_id: str
    image_type: str = "chest_xray"

class ImageAnalysisResponse(BaseModel):
    classification: Dict
    report: str
    confidence: float
    abnormalities_detected: bool
    recommendations: List[str]

# Agent Schemas
class AgentStatus(BaseModel):
    agent_id: str
    name: str
    status: str
    specialization: str
    message_count: int

class AgentMessage(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    type: str
    timestamp: str
    priority: int
