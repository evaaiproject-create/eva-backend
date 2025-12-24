"""
Utility functions and FastAPI dependencies.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.models import User
from app.services.auth_service import auth_service


# Security scheme for bearer token
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Validates the token
    3. Retrieves the user from Firestore
    4. Returns the User object
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.email}
    """
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to get the current active user.
    Can be extended to check if user is active/enabled.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: 400 if user is inactive
    """
    # Future: Add logic to check if user is active
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def generate_session_id(user_id: str, device_id: str) -> str:
    """
    Generate a unique session ID.
    
    Args:
        user_id: User identifier
        device_id: Device identifier
        
    Returns:
        Session ID string
    """
    from datetime import datetime
    import hashlib
    
    timestamp = datetime.utcnow().isoformat()
    content = f"{user_id}:{device_id}:{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()
