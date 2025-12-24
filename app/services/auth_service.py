"""
Authentication service using Google OAuth 2.0.
Handles user authentication and JWT token management.
"""
from google.oauth2 import id_token
from google.auth.transport import requests
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets

from app.config import settings
from app.models import User, UserRole
from app.services.firestore_service import firestore_service


class AuthService:
    """
    Authentication service for Eva backend.
    
    Handles:
    - Google OAuth token verification
    - JWT token generation and validation
    - User registration and login
    - User limit enforcement
    """
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
    
    def __init__(self):
        """Initialize authentication service."""
        self.google_client_id = settings.google_client_id
        self.secret_key = settings.api_secret_key
    
    async def verify_google_token(self, id_token_string: str) -> Optional[dict]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            id_token_string: Google ID token from OAuth
            
        Returns:
            User info dict with 'sub' (user ID), 'email', 'name'
            None if token is invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_string,
                requests.Request(),
                self.google_client_id
            )
            
            # Token is valid, return user info
            return {
                "sub": idinfo["sub"],  # Google user ID
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture")
            }
        except ValueError as e:
            # Invalid token
            print(f"Token verification failed: {e}")
            return None
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.ALGORITHM)
        
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[dict]:
        """
        Decode and verify JWT access token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def register_user(self, id_token_string: str, device_id: Optional[str] = None) -> Tuple[User, str]:
        """
        Register a new user with Google OAuth.
        
        Args:
            id_token_string: Google ID token from OAuth
            device_id: Optional device identifier
            
        Returns:
            Tuple of (User object, access token)
            
        Raises:
            ValueError: If token is invalid or user limit reached
        """
        # Verify Google token
        google_user = await self.verify_google_token(id_token_string)
        if not google_user:
            raise ValueError("Invalid Google ID token")
        
        # Check if user already exists
        existing_user = await firestore_service.get_user(google_user["sub"])
        if existing_user:
            raise ValueError("User already registered")
        
        # Check user limit
        user_count = await firestore_service.count_users()
        if user_count >= settings.max_users:
            raise ValueError(f"Maximum user limit ({settings.max_users}) reached")
        
        # Create new user
        user = User(
            uid=google_user["sub"],
            email=google_user["email"],
            display_name=google_user.get("name"),
            role=UserRole.USER,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            devices=[device_id] if device_id else []
        )
        
        # Save to Firestore
        await firestore_service.create_user(user)
        
        # Generate access token
        access_token = self.create_access_token({"sub": user.uid, "email": user.email})
        
        return user, access_token
    
    async def login_user(self, id_token_string: str, device_id: Optional[str] = None) -> Tuple[User, str]:
        """
        Login existing user with Google OAuth.
        
        Args:
            id_token_string: Google ID token from OAuth
            device_id: Optional device identifier
            
        Returns:
            Tuple of (User object, access token)
            
        Raises:
            ValueError: If token is invalid or user not found
        """
        # Verify Google token
        google_user = await self.verify_google_token(id_token_string)
        if not google_user:
            raise ValueError("Invalid Google ID token")
        
        # Get user from Firestore
        user = await firestore_service.get_user(google_user["sub"])
        if not user:
            raise ValueError("User not found. Please register first.")
        
        # Update last login
        await firestore_service.update_user(user.uid, {"last_login": datetime.utcnow()})
        
        # Add device if provided and not already registered
        if device_id:
            await firestore_service.add_device_to_user(user.uid, device_id)
        
        # Generate access token
        access_token = self.create_access_token({"sub": user.uid, "email": user.email})
        
        return user, access_token
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            User object or None if token invalid
        """
        payload = self.decode_access_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await firestore_service.get_user(user_id)


# Global auth service instance
auth_service = AuthService()
