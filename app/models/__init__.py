"""
Data models for Eva backend.
Defines the structure of User, Session, and other core entities.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model representing a registered user.
    
    Attributes:
        uid: Unique user identifier from Google Auth
        email: User's email address
        display_name: User's display name
        role: User role (user/admin)
        created_at: Account creation timestamp
        last_login: Last login timestamp
        devices: List of registered device IDs
        preferences: User preferences and settings
    """
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    devices: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "uid": "google_user_123",
                "email": "user@example.com",
                "display_name": "John Doe",
                "role": "user",
                "devices": ["device_1", "device_2"],
                "preferences": {"theme": "dark", "notifications": True}
            }
        }


class SessionData(BaseModel):
    """
    Session data for cross-device syncing.
    
    Attributes:
        session_id: Unique session identifier
        user_id: Associated user ID
        device_id: Device identifier
        data: Session data payload
        created_at: Session creation time
        updated_at: Last update time
        expires_at: Session expiration time
    """
    session_id: str
    user_id: str
    device_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class FunctionCall(BaseModel):
    """
    Model for function calling requests.
    
    Attributes:
        function_name: Name of the function to call
        parameters: Function parameters
        user_id: User making the request
        device_id: Device making the request
        timestamp: Call timestamp
    """
    function_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    device_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FunctionResponse(BaseModel):
    """
    Response from a function call.
    
    Attributes:
        success: Whether the call succeeded
        result: Function result data
        error: Error message if failed
        execution_time: Time taken to execute (seconds)
    """
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class UserRegistration(BaseModel):
    """Model for user registration requests."""
    id_token: str  # Google ID token from OAuth
    device_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Model for login requests."""
    id_token: str  # Google ID token from OAuth
    device_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Model for authentication token responses."""
    access_token: str
    token_type: str = "bearer"
    user: User
