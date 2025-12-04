from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from api.schemas import ImageAnalysisRequest, ImageAnalysisResponse
from pathlib import Path
import shutil
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("./uploads/medical_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_medical_image(
    patient_id: str,
    image_type: str,
    file: UploadFile = File(...)
):
    """Upload medical image (X-ray, CT scan, etc.)"""
    try:
        logger.info(f"📸 Uploading {image_type} for patient {patient_id}")
        
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save file
        file_path = UPLOAD_DIR / f"{patient_id}_{image_type}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✅ Image saved to {file_path}")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "size_bytes": file_path.stat().st_size
        }
        
    except Exception as e:
        logger.error(f"❌ Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_medical_image(
    request: Request,
    patient_id: str,
    image_path: str,
    image_type: str = "chest_xray"
):
    """Analyze uploaded medical image"""
    try:
        logger.info(f"🔬 Analyzing {image_type} for patient {patient_id}")
        
        # Get Imaging Agent
        agents = request.app.state.agents
        imaging_agent = agents.get("img-1")
        
        if not imaging_agent:
            raise HTTPException(status_code=500, detail="Imaging agent not available")
        
        # Load imaging model if not already loaded
        if imaging_agent.model is None:
            await imaging_agent.load_imaging_model()
        
        # Analyze image
        result = await imaging_agent.process({
            "image_path": image_path,
            "image_type": image_type,
            "patient_id": patient_id
        })
        
        return ImageAnalysisResponse(
            classification=result["classification"],
            report=result["report"],
            confidence=result["confidence"],
            abnormalities_detected=result["abnormalities_detected"],
            recommendations=result["recommendations"]
        )
        
    except Exception as e:
        logger.error(f"❌ Image analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}/images")
async def get_patient_images(patient_id: str):
    """Get list of patient's uploaded images"""
    try:
        # Find all images for this patient
        patient_images = list(UPLOAD_DIR.glob(f"{patient_id}_*"))
        
        images = []
        for img_path in patient_images:
            images.append({
                "filename": img_path.name,
                "path": str(img_path),
                "size_bytes": img_path.stat().st_size,
                "uploaded_at": img_path.stat().st_mtime
            })
        
        return {
            "patient_id": patient_id,
            "count": len(images),
            "images": images
        }
        
    except Exception as e:
        logger.error(f"❌ Image list error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
