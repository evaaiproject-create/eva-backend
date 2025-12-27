"""
Conversation service for Eva.
Handles AI-powered text-based interactions with state management.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import settings
from app.services.memory_service import memory_service


class ConversationService:
    """
    Conversation service for AI-powered chat interactions.
    
    Features:
    - Text-based conversation with AI
    - Conversation state tracking
    - Integration with memory service
    - Support for multiple AI models
    """
    
    # Default system prompt for Eva
    DEFAULT_SYSTEM_PROMPT = """You are Eva, a helpful and friendly personal assistant inspired by JARVIS and Baymax.

Your personality:
- Helpful and proactive
- Professional yet warm
- Concise but thorough
- Remembers previous conversations
- Anticipates user needs

When responding:
- Be conversational and natural
- Provide actionable information
- Ask clarifying questions when needed
- Reference past conversations when relevant"""
    
    def __init__(self):
        """Initialize conversation service."""
        self._openai_client = None
    
    def _get_openai_client(self):
        """Get OpenAI client (lazy initialization)."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        
        return self._openai_client
    
    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        include_memory: bool = True,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate a response.
        
        Args:
            user_id: User identifier
            message: User's message
            session_id: Optional session for context
            system_prompt: Custom system prompt (uses default if None)
            include_memory: Whether to include long-term memory
            model: OpenAI model to use
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Response dictionary with assistant's reply
        """
        try:
            client = self._get_openai_client()
            
            # Build context with memory
            context = await memory_service.build_context(
                user_id=user_id,
                include_long_term=include_memory,
                short_term_limit=10,
                long_term_limit=5
            )
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT}
            ]
            
            # Add memory context
            messages.extend(context)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Save user message to short-term context
            await memory_service.add_message(
                user_id=user_id,
                role="user",
                content=message,
                session_id=session_id
            )
            
            # Generate response
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            assistant_message = response.choices[0].message.content
            
            # Save assistant response to short-term context
            await memory_service.add_message(
                user_id=user_id,
                role="assistant",
                content=assistant_message,
                session_id=session_id
            )
            
            return {
                "success": True,
                "message": assistant_message,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "error": str(e)
            }
    
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            session_id: Optional session filter
            limit: Maximum messages to return
            
        Returns:
            List of messages with metadata
        """
        return await memory_service.get_recent_messages(
            user_id=user_id,
            limit=limit,
            session_id=session_id
        )
    
    async def clear_conversation(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear conversation history.
        
        Args:
            user_id: User identifier
            session_id: Optional session to clear
            
        Returns:
            Result with count of cleared messages
        """
        count = await memory_service.clear_short_term_context(user_id, session_id)
        return {
            "success": True,
            "messages_cleared": count
        }
    
    async def analyze_intent(
        self,
        message: str
    ) -> Dict[str, Any]:
        """
        Analyze user intent from a message.
        
        Used for:
        - Detecting interruptions
        - Classifying message types
        - Identifying commands vs. conversation
        
        Args:
            message: User's message
            
        Returns:
            Intent analysis result
        """
        # Simple rule-based intent detection
        message_lower = message.lower().strip()
        
        # Acknowledgment patterns
        acknowledgments = ["okay", "ok", "umhmm", "uh huh", "yeah", "yes", "no", "got it", "sure"]
        
        # Command patterns
        command_prefixes = ["set", "create", "add", "delete", "remove", "show", "list", "get"]
        
        # Interruption patterns
        interrupt_patterns = ["stop", "wait", "hold on", "pause", "cancel", "never mind"]
        
        intent = {
            "type": "conversation",  # Default type
            "is_acknowledgment": False,
            "is_command": False,
            "is_interruption": False,
            "confidence": 0.7
        }
        
        # Check for acknowledgment (exact match or contained in message)
        for ack in acknowledgments:
            if message_lower == ack or (ack in message_lower and len(message_lower.split()) <= 3):
                intent["is_acknowledgment"] = True
                intent["type"] = "acknowledgment"
                intent["confidence"] = 0.9
                break
        
        # Check for command (only if not already classified)
        if not intent["is_acknowledgment"]:
            first_word = message_lower.split()[0] if message_lower else ""
            if first_word in command_prefixes:
                intent["is_command"] = True
                intent["type"] = "command"
                intent["confidence"] = 0.85
        
        # Check for interruption (takes precedence)
        for pattern in interrupt_patterns:
            if pattern in message_lower:
                intent["is_interruption"] = True
                intent["type"] = "interruption"
                intent["confidence"] = 0.9
                break
        
        return intent
    
    async def compress_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Compress short-term memory to long-term.
        
        Summarizes recent conversations and extracts key facts.
        
        Args:
            user_id: User identifier
            
        Returns:
            Compression result
        """
        return await memory_service.compress_to_long_term(user_id)


# Global conversation service instance
conversation_service = ConversationService()
