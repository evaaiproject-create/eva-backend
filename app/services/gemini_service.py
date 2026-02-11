"""
================================================================================
GEMINI AI SERVICE FOR EVA
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

RESPONSE STYLE:
- For simple questions: 1-2 sentences
- For explanations: Use bullet points or numbered lists
- For emotional support: Be empathetic and understanding
"""


class GeminiService:
    """
    Service class for interacting with Google's Gemini AI.
    """

    def __init__(self):
        # Validate API key at startup
        if not settings.google_api_key:
            print("⚠️  WARNING: GOOGLE_API_KEY is not set.")

        # Create the google-genai client
        # Removed 'v1alpha' to use the stable v1 API for better reliability
        self.client = genai.Client(
            api_key=settings.google_api_key
        )

        # Updated to the stable Gemini 2.0 Flash model ID
        self.model_id = "gemini-2.0-flash"

        # System instruction for EVA's personality
        self.system_instruction = EVA_SYSTEM_INSTRUCTION

        # Store for conversation histories
        self._conversation_histories: Dict[str, List[types.Content]] = {}

    # ==========================================================================
    # CONVERSATION HISTORY MANAGEMENT
    # ==========================================================================

    def _get_session_key(self, user_id: str, conversation_id: Optional[str] = None) -> str:
        return f"{user_id}:{conversation_id or 'default'}"

    def _get_history(self, user_id: str, conversation_id: Optional[str] = None) -> List[types.Content]:
        key = self._get_session_key(user_id, conversation_id)
        if key not in self._conversation_histories:
            self._conversation_histories[key] = []
        return self._conversation_histories[key]

    def _append_to_history(self, user_id: str, conversation_id: Optional[str], role: str, text: str) -> None:
        history = self._get_history(user_id, conversation_id)
        history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    # ==========================================================================
    # TEXT CHAT
    # ==========================================================================

    async def send_message(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> str:
        try:
            history = self._get_history(user_id, conversation_id)
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
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

            # Persist history
            self._append_to_history(user_id, conversation_id, "user", message)
            self._append_to_history(user_id, conversation_id, "model", response_text)

            return response_text

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "I'm sorry, I encountered an issue processing your request. Please try again."

    # ==========================================================================
    # STREAMING CHAT
    # ==========================================================================

    async def send_message_stream(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        try:
            history = self._get_history(user_id, conversation_id)
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
            contents = history + [user_content]

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

            self._append_to_history(user_id, conversation_id, "user", message)
            self._append_to_history(user_id, conversation_id, "model", full_response)

        except Exception as e:
            print(f"Gemini Streaming Error: {e}")
            yield "I'm sorry, I encountered an issue. Please try again."

    # ==========================================================================
    # CONVERSATION MANAGEMENT
    # ==========================================================================

    def clear_conversation(self, user_id: str, conversation_id: Optional[str] = None) -> None:
        key = self._get_session_key(user_id, conversation_id)
        if key in self._conversation_histories:
            del self._conversation_histories[key]

# Singleton instance
gemini_service = GeminiService()
