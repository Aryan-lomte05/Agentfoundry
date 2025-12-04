import hashlib
import secrets
from typing import Optional
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)

def hash_data(data: str) -> str:
    """Hash data using SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()

