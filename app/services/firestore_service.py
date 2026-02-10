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
        """
        Initialize the service. 
        We use lazy initialization for the db client to prevent 
        crashes during the import phase.
        """
        self.db = None

    def _initialize(self):
        """
        Connects to Firestore using the project ID from settings.
        This is called automatically by every method before performing an operation.
        """
        if self.db is None:
            # If settings.google_cloud_project is empty, firestore.Client() 
            # will attempt to auto-detect from the environment.
            self.db = firestore.Client(
                project=settings.google_cloud_project,
                database="(default)"
            )

    # ================================================================================
    # CHAT MESSAGE OPERATIONS
    # ================================================================================

    async def save_chat_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        content: str,
        role: str,
        timestamp: datetime
    ) -> None:
        """Save a chat message to Firestore."""
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

    async def get_chat_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat messages for a conversation, ordered by timestamp."""
        self._initialize()
        
        query = (
            self.db.collection("chat_messages")
            .where("user_id", "==", user_id)
            .where("conversation_id", "==", conversation_id)
            .order_by("timestamp")
            .limit(limit)
        )
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    # ================================================================================
    # CONVERSATION OPERATIONS
    # ================================================================================

    async def create_conversation(
        self,
        user_id: str,
        conversation_id: str,
        title: str,
        created_at: datetime
    ) -> None:
        """Create a new conversation record."""
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

    async def update_conversation_metadata(
        self,
        user_id: str,
        conversation_id: str,
        last_message: str
    ) -> None:
        """Update metadata like timestamps and message count."""
        self._initialize()
        
        doc_id = f"{user_id}_{conversation_id}"
        doc_ref = self.db.collection("conversations").document(doc_id)
        
        if not doc_ref.get().exists:
            await self.create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                title=last_message[:30] + "..." if len(last_message) > 30 else last_message,
                created_at=datetime.utcnow()
            )
        
        doc_ref.update({
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": firestore.Increment(1),
            "last_message": last_message
        })

    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user, newest first."""
        self._initialize()
        
        query = (
            self.db.collection("conversations")
            .where("user_id", "==", user_id)
            .order_by("updated_at", direction=firestore.Query.DESCENDING)
        )
        
        docs = query.stream()
        
        conversations = []
        for doc in docs:
            data = doc.to_dict()
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            conversations.append(data)
        
        return conversations

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        """Permanently delete a conversation and all its messages."""
        self._initialize()
        
        conv_doc_id = f"{user_id}_{conversation_id}"
        self.db.collection("conversations").document(conv_doc_id).delete()
        
        messages_query = (
            self.db.collection("chat_messages")
            .where("user_id", "==", user_id)
            .where("conversation_id", "==", conversation_id)
        )
        
        batch = self.db.batch()
        docs = messages_query.stream()
        
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        
        if count > 0:
            batch.commit()

    # ================================================================================
    # USER OPERATIONS
    # ================================================================================

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user details by ID."""
        self._initialize()
        doc = self.db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else None

    async def create_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Create or update user details."""
        self._initialize()
        self.db.collection("users").document(user_id).set(user_data)

# Create the singleton instance used by the rest of the app
firestore_service = FirestoreService()
