import pytesseract
from PIL import Image
import re
from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Configure Tesseract path (Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path: str, lang: str = 'eng') -> str:
    """
    Extract text from image using Tesseract OCR
    
    Args:
        image_path: Path to image file
        lang: Language code (eng, hin, tam for Hindi/Tamil)
        
    Returns:
        str: Extracted text
    """
    try:
        logger.info(f"📄 Extracting text from {image_path}")
        
        image = Image.open(image_path)
        
        # OCR configuration
        custom_config = r'--oem 3 --psm 6'
        
        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
        
        logger.info(f"✅ Extracted {len(text)} characters")
        return text.strip()
        
    except Exception as e:
        logger.error(f"❌ OCR error: {str(e)}")
        return ""

def extract_medical_data(text: str) -> Dict:
    """
    Extract structured medical data from OCR text
    
    Args:
        text: OCR extracted text
        
    Returns:
        Dict: Structured medical data
    """
    logger.info("🔍 Extracting medical data from text")
    
    data = {
        "medications": [],
        "dosages": [],
        "lab_results": {},
        "dates": []
    }
    
    # Extract medications (common drug names)
    medication_patterns = [
        r'\b(paracetamol|ibuprofen|amoxicillin|azithromycin|metformin|amlodipine|omeprazole)\b',
        r'\b(aspirin|atorvastatin|lisinopril|levothyroxine|simvastatin)\b'
    ]
    
    for pattern in medication_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            med = match.group(0).title()
            if med not in data["medications"]:
                data["medications"].append(med)
    
    # Extract dosages (e.g., 500mg, 10ml)
    dosage_pattern = r'\b(\d+)\s*(mg|ml|g|mcg|units?)\b'
    dosages = re.findall(dosage_pattern, text, re.IGNORECASE)
    data["dosages"] = [f"{amount}{unit}" for amount, unit in dosages]
    
    # Extract lab values (e.g., HbA1c: 7.2%, Glucose: 120 mg/dL)
    lab_patterns = {
        'glucose': r'glucose[:\s]+(\d+\.?\d*)\s*mg/dl',
        'hba1c': r'hba1c[:\s]+(\d+\.?\d*)\s*%',
        'hemoglobin': r'hemoglobin[:\s]+(\d+\.?\d*)',
        'wbc': r'wbc[:\s]+(\d+\.?\d*)',
        'platelet': r'platelet[:\s]+(\d+\.?\d*)'
    }
    
    for test_name, pattern in lab_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["lab_results"][test_name] = match.group(1)
    
    # Extract dates (DD/MM/YYYY or DD-MM-YYYY)
    date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
    dates = re.findall(date_pattern, text)
    data["dates"] = dates
    
    logger.info(f"✅ Extracted: {len(data['medications'])} medications, {len(data['lab_results'])} lab results")
    
    return data
