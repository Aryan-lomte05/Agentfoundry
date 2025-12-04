from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from api.schemas import PatientCreate, PatientHistoryUpload
from database.models import Patient, PatientHistory
from database.database import get_db
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/create")
async def create_patient(patient: PatientCreate):
    """Create new patient profile"""
    try:
        logger.info(f"👤 Creating patient profile: {patient.patient_id}")
        
        db = next(get_db())
        
        # Check if patient exists
        existing = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Patient already exists")
        
        # Create patient
        new_patient = Patient(
            patient_id=patient.patient_id,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            phone=patient.phone,
            location=patient.location
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        return {
            "success": True,
            "patient_id": patient.patient_id,
            "message": "Patient profile created successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Patient creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient profile"""
    try:
        db = next(get_db())
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "phone": patient.phone,
            "location": patient.location
        }
        
    except Exception as e:
        logger.error(f"❌ Patient retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/upload")
async def upload_history(history: PatientHistoryUpload):
    """Upload patient medical history"""
    try:
        logger.info(f"📄 Uploading history for patient {history.patient_id}")
        
        db = next(get_db())
        
        # Create history record
        new_record = PatientHistory(
            patient_id=history.patient_id,
            record_type=history.record_type,
            content=history.content,
            diagnosis=history.diagnosis,
            medications=history.medications or [],
            created_at=datetime.now()
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        # Add to RAG vector store
        from rag.knowledge_bases import get_kb_manager
        kb_manager = get_kb_manager()
        
        # Store in patient-specific knowledge base (if needed)
        # For now, just log success
        
        return {
            "success": True,
            "record_id": new_record.id,
            "message": "Medical history uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ History upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}/history")
async def get_patient_history(patient_id: str, limit: int = 10):
    """Get patient medical history"""
    try:
        db = next(get_db())
        
        records = db.query(PatientHistory).filter(
            PatientHistory.patient_id == patient_id
        ).order_by(PatientHistory.created_at.desc()).limit(limit).all()
        
        return {
            "patient_id": patient_id,
            "count": len(records),
            "records": [
                {
                    "id": r.id,
                    "date": r.created_at.isoformat() if hasattr(r, 'created_at') else None,
                    "type": r.record_type,
                    "content": r.content,
                    "diagnosis": r.diagnosis,
                    "medications": r.medications
                }
                for r in records
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{patient_id}/history/{record_id}")
async def delete_history_record(patient_id: str, record_id: int):
    """Delete medical history record"""
    try:
        db = next(get_db())
        
        record = db.query(PatientHistory).filter(
            PatientHistory.id == record_id,
            PatientHistory.patient_id == patient_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        db.delete(record)
        db.commit()
        
        return {
            "success": True,
            "message": "Record deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Record deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
