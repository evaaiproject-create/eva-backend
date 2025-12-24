"""
User management API routes.
Handles user profile operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models import User
from app.utils.dependencies import get_current_user
from app.services.firestore_service import firestore_service


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user's profile.
    
    Requires authentication via Bearer token.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        User profile information
    """
    return current_user


@router.get("/me/devices", response_model=List[str])
async def get_user_devices(current_user: User = Depends(get_current_user)) -> List[str]:
    """
    Get list of devices registered to the current user.
    
    This is useful for cross-device sync - knowing which devices
    the user has connected helps coordinate state synchronization.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        List of device IDs
    """
    return current_user.devices


@router.post("/me/devices/{device_id}")
async def add_device(device_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """
    Register a new device for the current user.
    
    Args:
        device_id: Unique device identifier
        current_user: Authenticated user from dependency
        
    Returns:
        Success message
    """
    await firestore_service.add_device_to_user(current_user.uid, device_id)
    return {"message": f"Device {device_id} added successfully"}


@router.put("/me/preferences")
async def update_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Update user preferences.
    
    Preferences can include:
    - UI theme
    - Notification settings
    - Language preferences
    - Any custom app settings
    
    Args:
        preferences: Dictionary of preference key-value pairs
        current_user: Authenticated user from dependency
        
    Returns:
        Success message
    """
    await firestore_service.update_user(current_user.uid, {"preferences": preferences})
    return {"message": "Preferences updated successfully"}


@router.get("/me/preferences")
async def get_preferences(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get user preferences.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        User preferences dictionary
    """
    return current_user.preferences
