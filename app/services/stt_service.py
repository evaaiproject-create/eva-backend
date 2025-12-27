"""
Speech-to-Text (STT) service for Eva.
Provides modular STT engine support with Whisper (via OpenAI) and Google Cloud STT.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import base64
import os

from app.config import settings


class STTEngine(ABC):
    """Abstract base class for STT engines."""
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en-US") -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., "en-US")
            
        Returns:
            Dictionary with transcription result:
            {
                "text": str,
                "confidence": float,
                "language": str
            }
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the engine name."""
        pass


class WhisperSTTEngine(STTEngine):
    """
    Whisper STT engine using OpenAI's API.
    Robust performance in noisy environments.
    """
    
    def __init__(self):
        """Initialize Whisper engine with OpenAI API."""
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = settings.openai_api_key
                if api_key:
                    self._client = OpenAI(api_key=api_key)
                else:
                    raise ValueError("OPENAI_API_KEY not configured")
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client
    
    async def transcribe(self, audio_data: bytes, language: str = "en-US") -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_data: Raw audio bytes (supports various formats)
            language: Language code
            
        Returns:
            Transcription result dictionary
        """
        import tempfile
        temp_path = None
        
        try:
            client = self._get_client()
            
            # Write audio to temporary file (Whisper API requires file)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            with open(temp_path, "rb") as audio_file:
                # Language code mapping (e.g., "en-US" -> "en")
                lang_code = language.split("-")[0] if "-" in language else language
                
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=lang_code
                )
                
                return {
                    "text": response.text,
                    "confidence": 1.0,  # Whisper doesn't provide confidence
                    "language": language,
                    "engine": "whisper"
                }
                
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "engine": "whisper",
                "error": str(e)
            }
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def get_name(self) -> str:
        return "whisper"


class GoogleSTTEngine(STTEngine):
    """
    Google Cloud Speech-to-Text engine.
    Good for production use with real-time streaming support.
    """
    
    def __init__(self):
        """Initialize Google Cloud STT client."""
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Google Cloud Speech client."""
        if self._client is None:
            try:
                from google.cloud import speech
                self._client = speech.SpeechClient()
            except ImportError:
                raise ImportError("google-cloud-speech not installed. Run: pip install google-cloud-speech")
        return self._client
    
    async def transcribe(self, audio_data: bytes, language: str = "en-US") -> Dict[str, Any]:
        """
        Transcribe audio using Google Cloud Speech-to-Text.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., "en-US")
            
        Returns:
            Transcription result dictionary
        """
        try:
            from google.cloud import speech
            
            client = self._get_client()
            
            # Configure audio settings
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
                enable_automatic_punctuation=True,
            )
            
            # Perform recognition
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                return {
                    "text": alternative.transcript,
                    "confidence": alternative.confidence,
                    "language": language,
                    "engine": "google"
                }
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": language,
                    "engine": "google"
                }
                
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "engine": "google",
                "error": str(e)
            }
    
    def get_name(self) -> str:
        return "google"


class STTService:
    """
    Main STT service that provides a unified interface to different STT engines.
    
    Usage:
        stt = STTService()
        result = await stt.transcribe(audio_bytes)
    """
    
    def __init__(self):
        """Initialize STT service with configured engine."""
        self._engines: Dict[str, STTEngine] = {}
        self._current_engine: Optional[STTEngine] = None
        
        # Register available engines
        self._engines["whisper"] = WhisperSTTEngine()
        self._engines["google"] = GoogleSTTEngine()
    
    def get_engine(self, engine_name: Optional[str] = None) -> STTEngine:
        """
        Get an STT engine by name.
        
        Args:
            engine_name: Engine name (whisper, google). Defaults to configured engine.
            
        Returns:
            STTEngine instance
        """
        if engine_name is None:
            engine_name = settings.stt_engine
        
        if engine_name not in self._engines:
            raise ValueError(f"Unknown STT engine: {engine_name}")
        
        return self._engines[engine_name]
    
    async def transcribe(
        self, 
        audio_data: bytes, 
        language: str = "en-US",
        engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using the configured engine.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code
            engine: Optional engine override
            
        Returns:
            Transcription result dictionary
        """
        stt_engine = self.get_engine(engine)
        return await stt_engine.transcribe(audio_data, language)
    
    def list_engines(self) -> list:
        """List available STT engines."""
        return list(self._engines.keys())
    
    def get_current_engine(self) -> str:
        """Get the currently configured engine name."""
        return settings.stt_engine


# Global STT service instance
stt_service = STTService()
