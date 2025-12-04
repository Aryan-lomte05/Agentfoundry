from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import shutil
from services.ocr_service import extract_text_from_image, extract_medical_data
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("./uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extract text from medical document using OCR"""
    try:
        logger.info(f"📄 OCR processing: {file.filename}")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text
        extracted_text = extract_text_from_image(str(file_path))
        
        # Extract structured medical data
        medical_data = extract_medical_data(extracted_text)
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_text": extracted_text,
            "medical_data": medical_data
        }
        
    except Exception as e:
        logger.error(f"❌ OCR error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-prescription")
async def process_prescription(patient_id: str, file: UploadFile = File(...)):
    """Process prescription document and extract medications"""
    try:
        logger.info(f"💊 Processing prescription for patient {patient_id}")
        
        # Save file
        file_path = UPLOAD_DIR / f"{patient_id}_prescription_{file.filename}"
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text
        text = extract_text_from_image(str(file_path))
        
        # Extract medications (simple pattern matching)
        medications = extract_medical_data(text).get("medications", [])
        
        # Store in patient history
        from database.database import get_db
        from database.models import PatientHistory
        from datetime import datetime
        
        db = next(get_db())
        
        new_record = PatientHistory(
            patient_id=patient_id,
            record_type="prescription",
            content=text,
            medications=medications,
            created_at=datetime.now()
        )
        
        db.add(new_record)
        db.commit()
        
        return {
            "success": True,
            "medications_found": len(medications),
            "medications": medications,
            "full_text": text
        }
        
    except Exception as e:
        logger.error(f"❌ Prescription processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-lab-report")
async def process_lab_report(patient_id: str, file: UploadFile = File(...)):
    """Process lab report and extract test results"""
    try:
        logger.info(f"🧪 Processing lab report for patient {patient_id}")
        
        # Save file
        file_path = UPLOAD_DIR / f"{patient_id}_labreport_{file.filename}"
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text
        text = extract_text_from_image(str(file_path))
        
        # Extract lab values (simple pattern matching)
        lab_data = extract_medical_data(text).get("lab_results", {})
        
        return {
            "success": True,
            "lab_results": lab_data,
            "full_text": text
        }
        
    except Exception as e:
        logger.error(f"❌ Lab report processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
