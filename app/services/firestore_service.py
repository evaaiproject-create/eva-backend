from google.cloud import firestore
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.config import settings

class FirestoreService:
    """
    Service class for interacting with Google Cloud Firestore.
    Handles storage and retrieval of chat history and user data.
    """

    def __init__(self):
        self.db = None

    def _initialize(self):
        if self.db is None:
            # Connect to your "default" database
            self.db = firestore.Client(
                project=settings.google_cloud_project,
                database="default"
            )

    # ================================================================================
    # CHAT MESSAGE OPERATIONS
    # ================================================================================

    async def save_chat_message(self, user_id: str, conversation_id: str, message_id: str, content: str, role: str, timestamp: datetime) -> None:
        self._initialize()
        doc_id = f"{user_id}_{conversation_id}_{message_id}"
        doc_ref = self.db.collection("chat_messages").document(doc_id)
        doc_ref.set({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "content": content,
            "role": role,
            "timestamp": timestamp.isoformat()
        })

    async def get_chat_messages(self, user_id: str, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        self._initialize()
        query = (self.db.collection("chat_messages")
                 .where("user_id", "==", user_id)
                 .where("conversation_id", "==", conversation_id)
                 .order_by("timestamp").limit(limit))
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    # ================================================================================
    # CONVERSATION OPERATIONS
    # ================================================================================

    async def create_conversation(self, user_id: str, conversation_id: str, title: str, created_at: datetime) -> None:
        self._initialize()
        doc_id = f"{user_id}_{conversation_id}"
        doc_ref = self.db.collection("conversations").document(doc_id)
        doc_ref.set({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "title": title,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "message_count": 0
        })

    async def update_conversation_metadata(self, user_id: str, conversation_id: str, last_message: str) -> None:
        self._initialize()
        doc_id = f"{user_id}_{conversation_id}"
        doc_ref = self.db.collection("conversations").document(doc_id)
        if not doc_ref.get().exists:
            await self.create_conversation(user_id, conversation_id, last_message[:30], datetime.utcnow())
        doc_ref.update({
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": firestore.Increment(1),
            "last_message": last_message
        })

    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        self._initialize()
        query = (self.db.collection("conversations")
                 .where("user_id", "==", user_id)
                 .order_by("updated_at", direction=firestore.Query.DESCENDING))
        docs = query.stream()
        conversations = []
        for doc in docs:
            data = doc.to_dict()
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            conversations.append(data)
        return conversations

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        self._initialize()
        self.db.collection("conversations").document(f"{user_id}_{conversation_id}").delete()
        messages_query = self.db.collection("chat_messages").where("user_id", "==", user_id).where("conversation_id", "==", conversation_id)
        batch = self.db.batch()
        count = 0
        for doc in messages_query.stream():
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        if count > 0: batch.commit()

    # ================================================================================
    # USER OPERATIONS
    # ================================================================================

    async def get_user(self, user_id: str) -> Optional[Any]:
        """Retrieve user details and return as a User object."""
        self._initialize()
        doc = self.db.collection("users").document(user_id).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Import here to avoid circular dependencies
        from app.models import User
        
        # Handle cases where Firestore dates were stored as strings
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("last_login"), str):
            data["last_login"] = datetime.fromisoformat(data["last_login"])
            
        return User(**data)

    async def create_user(self, user: Any) -> None:
        """Create a new user. Expects a User model object."""
        self._initialize()
        # Convert User model to dict
        user_data = user.dict() if hasattr(user, "dict") else user
        user_id = user_data.get("uid")
        
        # Ensure dates are stored in a consistent format
        if isinstance(user_data.get("created_at"), datetime):
            user_data["created_at"] = user_data["created_at"].isoformat()
        if isinstance(user_data.get("last_login"), datetime):
            user_data["last_login"] = user_data["last_login"].isoformat()
            
        self.db.collection("users").document(user_id).set(user_data)

    async def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """Update existing user data."""
        self._initialize()
        
        # Convert any datetime objects to strings before updating
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                clean_data[k] = v.isoformat()
            else:
                clean_data[k] = v
                
        self.db.collection("users").document(user_id).update(clean_data)

    async def add_device_to_user(self, user_id: str, device_id: str) -> None:
        """Add a device ID to the user's list of devices."""
        self._initialize()
        self.db.collection("users").document(user_id).update({
            "devices": firestore.ArrayUnion([device_id])
        })

    async def count_users(self) -> int:
        self._initialize()
        query = self.db.collection("users").count()
        result = query.get()
        return result[0][0].value

# Singleton instance
firestore_service = FirestoreService()
