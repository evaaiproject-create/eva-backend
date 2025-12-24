"""
Authentication API routes.
Handles user registration and login with Google OAuth.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict

from app.models import UserRegistration, LoginRequest, TokenResponse
from app.services.auth_service import auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(registration: UserRegistration) -> TokenResponse:
    """
    Register a new user with Google OAuth.
    
    This endpoint:
    1. Verifies the Google ID token
    2. Checks if user limit has been reached (max 5 users by default)
    3. Creates a new user in Firestore
    4. Returns an access token for the user
    
    Args:
        registration: UserRegistration with Google ID token and optional device_id
        
    Returns:
        TokenResponse with access token and user information
        
    Raises:
        HTTPException: 
            - 400 if token is invalid
            - 409 if user already exists
            - 403 if user limit reached
    """
    try:
        user, access_token = await auth_service.register_user(
            registration.id_token,
            registration.device_id
        )
        
        return TokenResponse(
            access_token=access_token,
            user=user
        )
        
    except ValueError as e:
        error_msg = str(e)
        
        if "already registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        elif "limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest) -> TokenResponse:
    """
    Login an existing user with Google OAuth.
    
    This endpoint:
    1. Verifies the Google ID token
    2. Retrieves the user from Firestore
    3. Updates last login timestamp
    4. Returns an access token for the user
    
    Args:
        login_request: LoginRequest with Google ID token and optional device_id
        
    Returns:
        TokenResponse with access token and user information
        
    Raises:
        HTTPException:
            - 400 if token is invalid
            - 404 if user not found
    """
    try:
        user, access_token = await auth_service.login_user(
            login_request.id_token,
            login_request.device_id
        )
        
        return TokenResponse(
            access_token=access_token,
            user=user
        )
        
    except ValueError as e:
        error_msg = str(e)
        
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.get("/verify")
async def verify_token(token: str) -> Dict[str, bool]:
    """
    Verify if a JWT token is valid.
    
    Args:
        token: JWT access token to verify
        
    Returns:
        Dictionary with valid: true/false
    """
    user = await auth_service.get_current_user(token)
    return {"valid": user is not None}
