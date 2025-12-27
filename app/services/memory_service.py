"""
Memory service for Eva.
Manages short-term and long-term conversation memory.

Structure in Firestore:
- users/{userId}/short_term_context/  - Recent conversations
- users/{userId}/long_term_memory/    - Summarized key facts
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib

from app.config import settings


class MemoryService:
    """
    Memory management service for Eva.
    
    Handles:
    - Short-term context: Recent conversations and messages
    - Long-term memory: Summarized facts, preferences, and important information
    - AI-powered summarization for memory compression
    
    Collections structure:
        users/{userId}/short_term_context/{contextId}
        users/{userId}/long_term_memory/{memoryId}
    """
    
    def __init__(self):
        """Initialize memory service."""
        self._db = None
        self._openai_client = None
        
        # Configuration
        self.max_short_term_messages = 50  # Keep last 50 messages
        self.short_term_expiry_hours = 24  # Expire short-term context after 24 hours
    
    def _get_db(self):
        """Get Firestore client (lazy initialization)."""
        if self._db is None:
            from google.cloud import firestore
            import os
            
            if settings.google_application_credentials:
                creds_path = settings.google_application_credentials
                if not os.path.isabs(creds_path):
                    creds_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        creds_path
                    )
                if os.path.exists(creds_path):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
            
            self._db = firestore.Client(project=settings.google_cloud_project)
        
        return self._db
    
    def _get_openai_client(self):
        """Get OpenAI client for summarization (lazy initialization)."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured for AI summarization")
            
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        
        return self._openai_client
    
    def _get_user_short_term_ref(self, user_id: str):
        """Get reference to user's short-term context collection."""
        db = self._get_db()
        return db.collection("users").document(user_id).collection("short_term_context")
    
    def _get_user_long_term_ref(self, user_id: str):
        """Get reference to user's long-term memory collection."""
        db = self._get_db()
        return db.collection("users").document(user_id).collection("long_term_memory")
    
    # ==================== Short-Term Context ====================
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to short-term context.
        
        Args:
            user_id: User identifier
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Optional session identifier
            metadata: Optional additional metadata
            
        Returns:
            Created message document
        """
        collection = self._get_user_short_term_ref(user_id)
        
        message_data = {
            "role": role,
            "content": content,
            "session_id": session_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=self.short_term_expiry_hours)
        }
        
        doc_ref = collection.add(message_data)
        message_data["id"] = doc_ref[1].id
        
        return message_data
    
    async def get_recent_messages(
        self,
        user_id: str,
        limit: int = 20,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from short-term context.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages
            session_id: Optional filter by session
            
        Returns:
            List of recent messages
        """
        collection = self._get_user_short_term_ref(user_id)
        
        query = collection.order_by("timestamp", direction="DESCENDING").limit(limit)
        
        if session_id:
            from google.cloud.firestore_v1.base_query import FieldFilter
            query = query.where(filter=FieldFilter("session_id", "==", session_id))
        
        docs = query.stream()
        messages = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            messages.append(data)
        
        # Return in chronological order
        return list(reversed(messages))
    
    async def get_conversation_context(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for AI model.
        
        Args:
            user_id: User identifier
            limit: Number of messages to include
            
        Returns:
            List of messages in OpenAI format [{"role": "...", "content": "..."}]
        """
        messages = await self.get_recent_messages(user_id, limit)
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    
    async def clear_short_term_context(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> int:
        """
        Clear short-term context for a user.
        
        Args:
            user_id: User identifier
            session_id: Optional session to clear (None = clear all)
            
        Returns:
            Number of messages deleted
        """
        collection = self._get_user_short_term_ref(user_id)
        
        if session_id:
            from google.cloud.firestore_v1.base_query import FieldFilter
            query = collection.where(filter=FieldFilter("session_id", "==", session_id))
        else:
            query = collection
        
        # Use batch delete for better performance
        db = self._get_db()
        batch = db.batch()
        docs = list(query.stream())
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Firestore batch has a limit of 500 operations
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
        
        # Commit remaining deletes
        if count % 500 != 0:
            batch.commit()
        
        return count
    
    # ==================== Long-Term Memory ====================
    
    async def save_memory(
        self,
        user_id: str,
        category: str,
        content: str,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save information to long-term memory.
        
        Args:
            user_id: User identifier
            category: Memory category (preferences, events, facts, goals)
            content: Memory content
            importance: Importance score (1-10)
            metadata: Additional metadata
            
        Returns:
            Created memory document
        """
        collection = self._get_user_long_term_ref(user_id)
        
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        memory_data = {
            "category": category,
            "content": content,
            "content_hash": content_hash,
            "importance": min(max(importance, 1), 10),  # Clamp 1-10
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "access_count": 0
        }
        
        doc_ref = collection.add(memory_data)
        memory_data["id"] = doc_ref[1].id
        
        return memory_data
    
    async def get_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get long-term memories for a user.
        
        Args:
            user_id: User identifier
            category: Optional category filter
            limit: Maximum number of memories
            
        Returns:
            List of memory documents
        """
        collection = self._get_user_long_term_ref(user_id)
        
        query = collection.order_by("importance", direction="DESCENDING").limit(limit)
        
        if category:
            from google.cloud.firestore_v1.base_query import FieldFilter
            query = query.where(filter=FieldFilter("category", "==", category))
        
        docs = query.stream()
        memories = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            memories.append(data)
        
        return memories
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search long-term memories (simple keyword search).
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching memories
        """
        # Get all memories and filter (simple implementation)
        # For production, consider using a proper search engine
        all_memories = await self.get_memories(user_id, limit=100)
        
        query_lower = query.lower()
        matching = [
            mem for mem in all_memories
            if query_lower in mem.get("content", "").lower()
        ]
        
        return matching[:limit]
    
    async def update_memory(
        self,
        user_id: str,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a long-term memory.
        
        Args:
            user_id: User identifier
            memory_id: Memory document ID
            updates: Fields to update
            
        Returns:
            Updated memory or None
        """
        collection = self._get_user_long_term_ref(user_id)
        doc_ref = collection.document(memory_id)
        
        if not doc_ref.get().exists:
            return None
        
        updates["updated_at"] = datetime.utcnow()
        doc_ref.update(updates)
        
        # Get updated document
        doc = doc_ref.get()
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a long-term memory.
        
        Args:
            user_id: User identifier
            memory_id: Memory document ID
            
        Returns:
            True if deleted, False if not found
        """
        collection = self._get_user_long_term_ref(user_id)
        doc_ref = collection.document(memory_id)
        
        if not doc_ref.get().exists:
            return False
        
        doc_ref.delete()
        return True
    
    # ==================== AI Summarization ====================
    
    async def summarize_conversation(
        self,
        user_id: str,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Summarize a conversation using AI and extract key facts.
        
        Args:
            user_id: User identifier
            messages: Messages to summarize (or fetch recent if None)
            
        Returns:
            Summary with extracted facts
        """
        if messages is None:
            messages = await self.get_conversation_context(user_id, limit=30)
        
        if not messages:
            return {"summary": "", "facts": [], "error": "No messages to summarize"}
        
        try:
            client = self._get_openai_client()
            
            # Format conversation for summarization
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ])
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this conversation and provide:
1. A brief summary (2-3 sentences)
2. Key facts about the user (interests, preferences, plans, events)
3. Important topics discussed

Format your response as JSON:
{
    "summary": "...",
    "facts": [
        {"category": "preference|interest|event|goal|fact", "content": "...", "importance": 1-10}
    ],
    "topics": ["topic1", "topic2"]
}"""
                    },
                    {
                        "role": "user",
                        "content": conversation_text
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            result_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = {
                    "summary": result_text,
                    "facts": [],
                    "topics": []
                }
            
            return result
            
        except Exception as e:
            return {
                "summary": "",
                "facts": [],
                "topics": [],
                "error": str(e)
            }
    
    async def compress_to_long_term(self, user_id: str) -> Dict[str, Any]:
        """
        Compress short-term context to long-term memory.
        
        Summarizes recent conversations and saves key facts to long-term memory.
        
        Args:
            user_id: User identifier
            
        Returns:
            Compression result with saved facts count
        """
        # Get summary of recent conversations
        summary_result = await self.summarize_conversation(user_id)
        
        if "error" in summary_result:
            return summary_result
        
        saved_facts = []
        
        # Save extracted facts to long-term memory
        for fact in summary_result.get("facts", []):
            memory = await self.save_memory(
                user_id=user_id,
                category=fact.get("category", "fact"),
                content=fact.get("content", ""),
                importance=fact.get("importance", 5),
                metadata={"source": "conversation_compression"}
            )
            saved_facts.append(memory)
        
        return {
            "summary": summary_result.get("summary", ""),
            "topics": summary_result.get("topics", []),
            "facts_saved": len(saved_facts),
            "facts": saved_facts
        }
    
    # ==================== Context Building ====================
    
    async def build_context(
        self,
        user_id: str,
        include_long_term: bool = True,
        short_term_limit: int = 10,
        long_term_limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Build a context for AI conversation that includes both short-term and long-term memory.
        
        Args:
            user_id: User identifier
            include_long_term: Whether to include long-term memory
            short_term_limit: Number of recent messages
            long_term_limit: Number of long-term memories
            
        Returns:
            List of messages suitable for AI model context
        """
        context = []
        
        # Add long-term memory as system context
        if include_long_term:
            memories = await self.get_memories(user_id, limit=long_term_limit)
            if memories:
                memory_text = "User information from previous conversations:\n"
                memory_text += "\n".join([
                    f"- {mem['content']}" for mem in memories
                ])
                context.append({
                    "role": "system",
                    "content": memory_text
                })
        
        # Add recent conversation
        recent = await self.get_conversation_context(user_id, limit=short_term_limit)
        context.extend(recent)
        
        return context


# Global memory service instance
memory_service = MemoryService()
