import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict

def generate_patient_id() -> str:
    """Generate unique patient ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"PAT-{timestamp}-{random_suffix}"

def hash_data(data: str) -> str:
    """Generate SHA-256 hash of data"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def format_medical_record(record: Dict[str, Any]) -> str:
    """Format medical record for display"""
    formatted = f"""
    === MEDICAL RECORD ===
    Date: {record.get('date', 'N/A')}
    Type: {record.get('type', 'N/A')}
    Diagnosis: {record.get('diagnosis', 'N/A')}
    """
    
    if record.get('medications'):
        formatted += "\nMedications:\n"
        for med in record['medications']:
            formatted += f"  - {med}\n"
    
    return formatted

def calculate_age_from_dob(dob: str) -> int:
    """Calculate age from date of birth (YYYY-MM-DD)"""
    from datetime import datetime
    
    birth_date = datetime.strptime(dob, "%Y-%m-%d")
    today = datetime.now()
    
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age
