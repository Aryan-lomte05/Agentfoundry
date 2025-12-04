from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """
    Verify JWT token and return user ID
    For hackathon: Simple token validation
    In production: Proper JWT verification
    """
    token = credentials.credentials
    
    # For demo: Accept any token that starts with "Bearer"
    # In production: Verify JWT signature
    
    if token:
        return "demo_user"
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )
