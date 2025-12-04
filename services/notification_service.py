from celery import Celery
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize Celery
celery_app = Celery(
    'healthfourvs',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def send_medication_reminder(patient_id: str, medication: str, time: str):
    """Send medication reminder notification"""
    logger.info(f"💊 Sending reminder to {patient_id}: {medication} at {time}")
    
    # In production: Send SMS/Email/Push notification
    # For demo: Just log
    
    return {
        "sent": True,
        "patient_id": patient_id,
        "medication": medication
    }

@celery_app.task
def send_emergency_alert(patient_id: str, doctor_id: str, message: str):
    """Send emergency alert to doctor"""
    logger.critical(f"🚨 Emergency alert: {patient_id} → {doctor_id}")
    
    # In production: Send urgent SMS/Call
    
    return {
        "sent": True,
        "doctor_id": doctor_id
    }

@celery_app.task
def send_token_reward_notification(patient_id: str, amount: int, reason: str):
    """Notify patient about token reward"""
    logger.info(f"🎁 Token reward notification: {patient_id} - {amount} tokens")
    
    return {
        "sent": True,
        "amount": amount
    }
