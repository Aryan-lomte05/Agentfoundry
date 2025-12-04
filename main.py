
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.routes import chat, patient, agents, blockchain, medical_images, ocr
from database.database import engine, Base
from agents.message_bus import MessageBus, get_message_bus
from agents import *
from models.model_loader import load_model
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting HealthFourUs Backend...")
    
    # Initialize database
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")
    
    # Load fine-tuned model
    logger.info("🧠 Loading fine-tuned BioMistral model...")
    model, tokenizer = await load_model()
    app.state.model = model
    app.state.tokenizer = tokenizer
    logger.info("✅ Model loaded successfully")
    
    # Initialize message bus and agents
    logger.info("🤖 Initializing multi-agent system...")
    message_bus = MessageBus()
    
    # Register all 9 agents
    from agents.patient_avatar_agent import PatientAvatarAgent
    from agents.diagnostic_agent import DiagnosticAgent
    from agents.imaging_agent import ImagingAgent
    from agents.treatment_agent import TreatmentAgent
    from agents.emergency_agent import EmergencyAgent
    from agents.records_agent import RecordsAgent
    from agents.doctor_notify_agent import DoctorNotifyAgent
    from agents.medication_agent import MedicationAgent
    from agents.blockchain_agent import BlockchainAgent
    
    agents_list = [
        PatientAvatarAgent("avatar-1", "Patient Avatar", model, tokenizer),
        DiagnosticAgent("diag-1", "Diagnostic Agent", model, tokenizer),
        ImagingAgent("img-1", "Imaging Agent"),
        TreatmentAgent("treat-1", "Treatment Agent", model, tokenizer),
        EmergencyAgent("emerg-1", "Emergency Triage"),
        RecordsAgent("rec-1", "Records Agent"),
        DoctorNotifyAgent("doc-1", "Doctor Notification"),
        MedicationAgent("med-1", "Medication Agent"),
        BlockchainAgent("chain-1", "Blockchain Agent")
    ]
    
    for agent in agents_list:
        message_bus.register_agent(agent)
        logger.info(f"  ✓ Registered {agent.name}")
    
    app.state.message_bus = message_bus
    app.state.agents = {agent.id: agent for agent in agents_list}
    logger.info("✅ Multi-agent system ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="HealthFourUs API",
    description="Multi-Agent Healthcare AI with Blockchain Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(patient.router, prefix="/api/patient", tags=["Patient"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["Blockchain"])
app.include_router(medical_images.router, prefix="/api/medical-images", tags=["Medical Images"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])

@app.get("/")
async def root():
    return {
        "message": "HealthFourUs API",
        "status": "operational",
        "agents": len(app.state.agents),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": hasattr(app.state, 'model'),
        "agents_active": len(app.state.agents) if hasattr(app.state, 'agents') else 0
    }

# WebSocket for real-time agent communication updates
@app.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    message_bus = get_message_bus()
    
    try:
        while True:
            # Send agent status updates
            if hasattr(message_bus, 'recent_messages'):
                for msg in message_bus.recent_messages[-10:]:
                    await websocket.send_json(msg)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
