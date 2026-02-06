    # ================================================================================
    # CHAT MESSAGE OPERATIONS
    # ================================================================================
    # These methods handle storing and retrieving chat messages.
    # Messages are stored in Firestore for:
    # - Cross-device sync (see chats on all your devices)
    # - Chat history (reload and see previous messages)
    # - Backup (messages survive app crashes/reinstalls)
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
        """
        Save a chat message to Firestore.
        
        FIRESTORE STRUCTURE:
            Collection: chat_messages
            Document ID: {user_id}_{conversation_id}_{message_id}
            Fields:
                - user_id: Who this message belongs to
                - conversation_id: Which conversation
                - message_id: Unique message identifier
                - content: The actual text
                - role: "user" or "assistant"
                - timestamp: When it was sent
        
        PARAMETERS:
            user_id: The user who owns this message
            conversation_id: Which conversation this belongs to
            message_id: Unique identifier for this message
            content: The message text
            role: "user" for user messages, "assistant" for EVA's responses
            timestamp: When the message was created
        """
        # Lazy initialize if needed
        self._initialize()
        
        # Create document reference
        doc_id = f"{user_id}_{conversation_id}_{message_id}"
        doc_ref = self.db.collection("chat_messages").document(doc_id)
        
        # Save the message
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
        """
        Get chat messages for a conversation.
        
        RETURNS:
            List of message dictionaries, ordered by timestamp (oldest first)
        
        PARAMETERS:
            user_id: The user to get messages for
            conversation_id: Which conversation
            limit: Maximum number of messages to return
        """
        self._initialize()
        
        # Query messages for this conversation
        query = (
            self.db.collection("chat_messages")
            .where("user_id", "==", user_id)
            .where("conversation_id", "==", conversation_id)
            .order_by("timestamp")
            .limit(limit)
        )
        
        docs = query.stream()
        
        return [doc.to_dict() for doc in docs]
    
    async def create_conversation(
        self,
        user_id: str,
        conversation_id: str,
        title: str,
        created_at: datetime
    ) -> None:
        """
        Create a new conversation record.
        
        FIRESTORE STRUCTURE:
            Collection: conversations
            Document ID: {user_id}_{conversation_id}
        """
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
        """
        Update conversation metadata (called after each message).
        
        UPDATES:
            - updated_at: Current timestamp
            - message_count: Increment by 1
            - last_message: Preview of latest message
        """
        self._initialize()
        
        doc_id = f"{user_id}_{conversation_id}"
        doc_ref = self.db.collection("conversations").document(doc_id)
        
        # Check if conversation exists
        if not doc_ref.get().exists:
            # Create it if it doesn't exist
            await self.create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                title=last_message[:30] + "..." if len(last_message) > 30 else last_message,
                created_at=datetime.utcnow()
            )
        
        # Update metadata
        doc_ref.update({
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": firestore.Increment(1),
            "last_message": last_message
        })
    
    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user.
        
        RETURNS:
            List of conversation metadata, ordered by most recent first
        """
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
            # Convert ISO strings back to datetime
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            conversations.append(data)
        
        return conversations
    
    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        """
        Delete a conversation and all its messages.
        
        WARNING: This is permanent!
        """
        self._initialize()
        
        # Delete conversation metadata
        conv_doc_id = f"{user_id}_{conversation_id}"
        self.db.collection("conversations").document(conv_doc_id).delete()
        
        # Delete all messages in this conversation
        messages_query = (
            self.db.collection("chat_messages")
            .where("user_id", "==", user_id)
            .where("conversation_id", "==", conversation_id)
        )
        
        # Delete in batches (Firestore best practice)
        batch = self.db.batch()
        docs = messages_query.stream()
        
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Commit every 500 (Firestore limit)
            if count >= 500:
                batch.commit()
                batch = self.db.batch()
                count = 0
        
        # Commit remaining
        if count > 0:
            batch.commit()


# This line should already exist at the end of your file - don't duplicate it!
# firestore_service = FirestoreService()
