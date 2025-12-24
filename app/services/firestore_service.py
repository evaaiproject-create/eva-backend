"""
Firestore service for data persistence.
Handles all interactions with Google Cloud Firestore.
"""
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from app.config import settings
from app.models import User, SessionData


class FirestoreService:
    """
    Service class for Firestore operations.
    
    This service manages:
    - User data storage and retrieval
    - Session data for cross-device sync
    - Function call history
    - User preferences
    
    Collections:
        - users: User profiles and settings
        - sessions: Active sessions for cross-device sync
        - function_calls: History of function invocations
    """
    
    def __init__(self):
        """
        Initialize Firestore client.
        Uses credentials from GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        # Set credentials path if specified in settings
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
        
        self.db = firestore.Client(project=settings.google_cloud_project)
        
        # Collection references
        self.users_collection = self.db.collection("users")
        self.sessions_collection = self.db.collection("sessions")
        self.function_calls_collection = self.db.collection("function_calls")
    
    # ==================== User Operations ====================
    
    async def create_user(self, user: User) -> User:
        """
        Create a new user in Firestore.
        
        Args:
            user: User object to create
            
        Returns:
            Created user object
            
        Raises:
            Exception if user already exists
        """
        user_ref = self.users_collection.document(user.uid)
        
        # Check if user already exists
        if user_ref.get().exists:
            raise ValueError(f"User {user.uid} already exists")
        
        # Create user document
        user_dict = user.model_dump(mode='json')
        user_ref.set(user_dict)
        
        return user
    
    async def get_user(self, uid: str) -> Optional[User]:
        """
        Get user by UID.
        
        Args:
            uid: User unique identifier
            
        Returns:
            User object or None if not found
        """
        user_ref = self.users_collection.document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        return User(**user_data)
    
    async def update_user(self, uid: str, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user data.
        
        Args:
            uid: User unique identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Updated user object or None if not found
        """
        user_ref = self.users_collection.document(uid)
        
        if not user_ref.get().exists:
            return None
        
        # Add updated_at timestamp
        update_data["last_login"] = datetime.utcnow()
        user_ref.update(update_data)
        
        return await self.get_user(uid)
    
    async def get_all_users(self) -> List[User]:
        """
        Get all users in the system.
        
        Returns:
            List of all users
        """
        users = []
        docs = self.users_collection.stream()
        
        for doc in docs:
            user_data = doc.to_dict()
            users.append(User(**user_data))
        
        return users
    
    async def count_users(self) -> int:
        """
        Count total number of users.
        
        Returns:
            Number of users in the system
        """
        users = await self.get_all_users()
        return len(users)
    
    async def add_device_to_user(self, uid: str, device_id: str) -> Optional[User]:
        """
        Add a device to user's device list.
        
        Args:
            uid: User unique identifier
            device_id: Device identifier to add
            
        Returns:
            Updated user object or None if not found
        """
        user = await self.get_user(uid)
        if not user:
            return None
        
        if device_id not in user.devices:
            user.devices.append(device_id)
            return await self.update_user(uid, {"devices": user.devices})
        
        return user
    
    # ==================== Session Operations ====================
    
    async def create_session(self, session: SessionData) -> SessionData:
        """
        Create a new session for cross-device sync.
        
        Args:
            session: SessionData object to create
            
        Returns:
            Created session object
        """
        session_ref = self.sessions_collection.document(session.session_id)
        session_dict = session.model_dump(mode='json')
        session_ref.set(session_dict)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData object or None if not found
        """
        session_ref = self.sessions_collection.document(session_id)
        session_doc = session_ref.get()
        
        if not session_doc.exists:
            return None
        
        session_data = session_doc.to_dict()
        return SessionData(**session_data)
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[SessionData]:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            data: Data to merge into session
            
        Returns:
            Updated session object or None if not found
        """
        session_ref = self.sessions_collection.document(session_id)
        
        if not session_ref.get().exists:
            return None
        
        update_data = {
            "data": data,
            "updated_at": datetime.utcnow()
        }
        session_ref.update(update_data)
        
        return await self.get_session(session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user's sessions
        """
        sessions = []
        query = self.sessions_collection.where(filter=FieldFilter("user_id", "==", user_id))
        docs = query.stream()
        
        for doc in docs:
            session_data = doc.to_dict()
            sessions.append(SessionData(**session_data))
        
        return sessions
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        session_ref = self.sessions_collection.document(session_id)
        
        if not session_ref.get().exists:
            return False
        
        session_ref.delete()
        return True
    
    # ==================== Function Call History ====================
    
    async def log_function_call(self, function_name: str, parameters: Dict[str, Any], 
                                user_id: str, result: Dict[str, Any]) -> str:
        """
        Log a function call for history/analytics.
        
        Args:
            function_name: Name of the function called
            parameters: Parameters passed to function
            user_id: User who made the call
            result: Result of the function call
            
        Returns:
            Document ID of the logged call
        """
        call_data = {
            "function_name": function_name,
            "parameters": parameters,
            "user_id": user_id,
            "result": result,
            "timestamp": datetime.utcnow()
        }
        
        doc_ref = self.function_calls_collection.add(call_data)
        return doc_ref[1].id
    
    async def get_user_function_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get function call history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of function call records
        """
        query = (self.function_calls_collection
                .where(filter=FieldFilter("user_id", "==", user_id))
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit))
        
        docs = query.stream()
        history = []
        
        for doc in docs:
            history.append(doc.to_dict())
        
        return history


# Global Firestore service instance
firestore_service = FirestoreService()
