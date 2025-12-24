"""
Session management API routes.
Handles cross-device synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models import User, SessionData
from app.utils.dependencies import get_current_user, generate_session_id
from app.services.firestore_service import firestore_service


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/", response_model=SessionData, status_code=status.HTTP_201_CREATED)
async def create_session(
    device_id: str,
    initial_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user)
) -> SessionData:
    """
    Create a new session for cross-device sync.
    
    Sessions allow seamless experiences across devices by storing
    and synchronizing state data. For example:
    - Conversation history
    - Current context
    - App state
    - User actions in progress
    
    Args:
        device_id: Device identifier creating the session
        initial_data: Optional initial session data
        current_user: Authenticated user from dependency
        
    Returns:
        Created SessionData object
    """
    session_id = generate_session_id(current_user.uid, device_id)
    
    session = SessionData(
        session_id=session_id,
        user_id=current_user.uid,
        device_id=device_id,
        data=initial_data
    )
    
    await firestore_service.create_session(session)
    return session


@router.get("/", response_model=List[SessionData])
async def get_user_sessions(current_user: User = Depends(get_current_user)) -> List[SessionData]:
    """
    Get all sessions for the current user.
    
    This allows a device to discover and sync with sessions
    from other devices.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        List of user's sessions
    """
    sessions = await firestore_service.get_user_sessions(current_user.uid)
    return sessions


@router.get("/{session_id}", response_model=SessionData)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> SessionData:
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user from dependency
        
    Returns:
        SessionData object
        
    Raises:
        HTTPException: 404 if session not found or 403 if not owned by user
    """
    session = await firestore_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify session belongs to current user
    if session.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session


@router.put("/{session_id}", response_model=SessionData)
async def update_session(
    session_id: str,
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> SessionData:
    """
    Update session data for cross-device sync.
    
    This endpoint is used to push state updates from one device
    that can then be pulled by other devices.
    
    Args:
        session_id: Session identifier
        data: New session data (will be merged)
        current_user: Authenticated user from dependency
        
    Returns:
        Updated SessionData object
        
    Raises:
        HTTPException: 404 if session not found or 403 if not owned by user
    """
    # Verify session exists and belongs to user
    session = await firestore_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this session"
        )
    
    # Update session
    updated_session = await firestore_service.update_session(session_id, data)
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )
    
    return updated_session


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user from dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if session not found or 403 if not owned by user
    """
    # Verify session exists and belongs to user
    session = await firestore_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session"
        )
    
    # Delete session
    success = await firestore_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
    
    return {"message": "Session deleted successfully"}
