"""
================================================================================
GEMINI AI SERVICE FOR EVA
================================================================================

PURPOSE:
    This file is the "brain" of EVA. It handles all communication with Google's
    Gemini AI model. When a user sends a message, this service:
    1. Takes the user's message
    2. Sends it to Google's Gemini AI
    3. Returns the AI's response

GEMINI 2.0 FLASH:
    We use the "gemini-2.0-flash-exp" model via the new google-genai SDK which
    supports:
    - Text conversations (chat)
    - Emotional tone detection
    - Real-time streaming responses (for voice calls)
    - Live API for bidirectional audio streaming (future)

SDK NOTE:
    This uses the NEW google-genai SDK (from google import genai) which is
    required for the Gemini 2.0 Live API. This replaces the older
    google.generativeai SDK.

    Install with: pip install google-genai

CONFIGURATION:
    - Uses GOOGLE_API_KEY from environment variables
    - Model: gemini-2.0-flash-exp (chosen for speed + Live API support)

================================================================================
"""

from google import genai
from google.genai import types
from typing import Optional, AsyncGenerator, Dict, Any, List
from datetime import datetime
import asyncio

from app.config import settings


# ==============================================================================
# EVA SYSTEM INSTRUCTION
# ==============================================================================
# This tells the AI how to behave in every conversation.
# Extracted as a module-level constant so it can be reused across
# both regular chat and live sessions.
# ==============================================================================

EVA_SYSTEM_INSTRUCTION = """
You are EVA, a personal AI assistant inspired by JARVIS and Baymax.

YOUR PERSONALITY:
- Warm, friendly, and approachable (like Baymax)
- Intelligent and capable (like JARVIS)
- Concise but helpful - don't be overly verbose
- Use a conversational tone, not robotic

YOUR CAPABILITIES:
- You can help with questions, tasks, and conversation
- You remember context within a conversation
- You can detect emotional tone and respond appropriately

GUIDELINES:
- Keep responses concise unless the user asks for detail
- Be proactive in offering help when appropriate
- If you don't know something, say so honestly
- Never pretend to have capabilities you don't have

RESPONSE STYLE:
- For simple questions: 1-2 sentences
- For explanations: Use bullet points or numbered lists
- For emotional support: Be empathetic and understanding
"""


class GeminiService:
    """
    Service class for interacting with Google's Gemini AI.

    This class manages:
    - Initializing the Gemini AI client (new google-genai SDK)
    - Sending messages and receiving responses
    - Maintaining conversation history for context
    - Streaming responses for real-time voice calls
    - Live API sessions for bidirectional audio (future)

    ATTRIBUTES:
        model_id (str): The Gemini model version we're using
        client: The google-genai Client instance

    USAGE EXAMPLE:
        service = GeminiService()
        response = await service.send_message("Hello!", user_id="user123")
        print(response)  # "Hello! I'm EVA, how can I help you today?"
    """

    def __init__(self):
        """
        Initialize the Gemini AI service.

        WHAT THIS DOES:
            1. Creates a google-genai Client with the API key
            2. Sets up EVA's personality (system instruction)
            3. Validates the API key is present

        NOTE: The API key comes from the GOOGLE_API_KEY environment variable.
              This is set in your .env file or Cloud Run configuration.
        """
        # Validate API key at startup
        if not settings.google_api_key:
            print(
                "⚠️  WARNING: GOOGLE_API_KEY is not set. "
                "Gemini AI calls will fail. "
                "Set it via environment variable on Cloud Run."
            )

        # Create the google-genai client
        # http_options with api_version='v1alpha' is required for Live API features
        self.client = genai.Client(
            api_key=settings.google_api_key,
            http_options={"api_version": "v1alpha"},
        )

        # The model ID — using Gemini 2.0 Flash Exp for:
        # - Fast response times (important for real-time chat)
        # - Live API support (bidirectional audio streaming)
        # - Emotional tone detection (understands user's mood)
        # - Cost efficiency (flash models are cheaper)
        self.model_id = "gemini-2.0-flash-exp"

        # System instruction for EVA's personality
        self.system_instruction = EVA_SYSTEM_INSTRUCTION

        # Store for conversation histories
        # Key: "user_id:conversation_id", Value: list of content dicts
        # This allows us to maintain conversation history per user
        self._conversation_histories: Dict[str, List[types.Content]] = {}

    # ==========================================================================
    # CONVERSATION HISTORY MANAGEMENT
    # ==========================================================================

    def _get_session_key(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> str:
        """Build a unique key for a user's conversation."""
        return f"{user_id}:{conversation_id or 'default'}"

    def _get_history(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> List[types.Content]:
        """
        Get the conversation history for a user, creating an empty one if needed.

        WHY THIS MATTERS:
            Without history, the AI forgets everything between messages.
            With history, it can say things like "As I mentioned earlier..."
        """
        key = self._get_session_key(user_id, conversation_id)
        if key not in self._conversation_histories:
            self._conversation_histories[key] = []
        return self._conversation_histories[key]

    def _append_to_history(
        self,
        user_id: str,
        conversation_id: Optional[str],
        role: str,
        text: str,
    ) -> None:
        """Append a message to the conversation history."""
        history = self._get_history(user_id, conversation_id)
        history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    # ==========================================================================
    # TEXT CHAT — regular request/response
    # ==========================================================================

    async def send_message(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        Send a message to EVA and get a response.

        THIS IS THE MAIN METHOD — Used for regular text chat.

        PARAMETERS:
            message: What the user said (e.g., "What's the weather?")
            user_id: Who is asking (e.g., "user_abc123")
            conversation_id: Which conversation this belongs to

        RETURNS:
            EVA's response text

        ERROR HANDLING:
            If something goes wrong (API error, network issue), this catches
            the error and returns a friendly error message instead of crashing.
        """
        try:
            # Build the contents list: history + new user message
            history = self._get_history(user_id, conversation_id)

            # Create the new user message
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )

            # Full contents = history + current message
            contents = history + [user_content]

            # Call Gemini
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                ),
            )

            response_text = response.text

            # Persist both messages in history for future context
            self._append_to_history(user_id, conversation_id, "user", message)
            self._append_to_history(
                user_id, conversation_id, "model", response_text
            )

            return response_text

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return (
                "I'm sorry, I encountered an issue processing your request. "
                "Please try again."
            )

    # ==========================================================================
    # STREAMING CHAT — for reduced latency / SSE endpoints
    # ==========================================================================

    async def send_message_stream(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response in real-time.

        THIS IS FOR VOICE CALLS — Streams words as they're generated.

        WHAT IS STREAMING?
            Instead of waiting for the complete response, we get words
            as the AI generates them. This reduces perceived latency.

        YIELDS:
            Chunks of text as they're generated

        EXAMPLE:
            async for chunk in gemini_service.send_message_stream(
                "Tell me a story", "user123"
            ):
                print(chunk, end="")
        """
        try:
            history = self._get_history(user_id, conversation_id)
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
            contents = history + [user_content]

            # Use streaming generation
            response_stream = self.client.models.generate_content_stream(
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                ),
            )

            full_response = ""
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

            # Persist history after streaming completes
            self._append_to_history(user_id, conversation_id, "user", message)
            self._append_to_history(
                user_id, conversation_id, "model", full_response
            )

        except Exception as e:
            print(f"Gemini Streaming Error: {e}")
            yield "I'm sorry, I encountered an issue. Please try again."

    # ==========================================================================
    # CONVERSATION MANAGEMENT
    # ==========================================================================

    def clear_conversation(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> None:
        """
        Clear a user's conversation history.

        WHEN TO USE:
            - User starts a "New Chat"
            - User explicitly asks to "forget" the conversation
            - Conversation gets too long (memory management)
        """
        key = self._get_session_key(user_id, conversation_id)
        if key in self._conversation_histories:
            del self._conversation_histories[key]

    def get_active_conversations(self, user_id: str) -> List[str]:
        """
        Get list of active conversation IDs for a user.

        RETURNS:
            List of conversation IDs that have in-memory histories
        """
        prefix = f"{user_id}:"
        return [
            key.replace(prefix, "")
            for key in self._conversation_histories
            if key.startswith(prefix)
        ]


# Create a singleton instance
# This means the entire application shares one GeminiService
# Benefits: Efficient memory use, shared conversation state
gemini_service = GeminiService()
