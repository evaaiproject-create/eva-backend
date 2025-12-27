"""
Speech API routes.
Handles STT (Speech-to-Text) and TTS (Text-to-Speech) operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
import base64

from app.models import User
from app.utils.dependencies import get_current_user
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service


router = APIRouter(prefix="/speech", tags=["Speech"])


# ==================== STT Endpoints ====================

@router.post("/transcribe", response_model=Dict[str, Any])
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "en-US",
    engine: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Transcribe audio to text using configured STT engine.
    
    Supports Whisper (via OpenAI) and Google Cloud Speech-to-Text.
    
    Args:
        file: Audio file (WAV, MP3, etc.)
        language: Language code (e.g., "en-US")
        engine: Optional engine override (whisper, google)
        current_user: Authenticated user
        
    Returns:
        Transcription result with text and confidence
    """
    try:
        # Read audio content
        audio_data = await file.read()
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )
        
        # Transcribe
        result = await stt_service.transcribe(
            audio_data=audio_data,
            language=language,
            engine=engine
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


class TranscribeBase64Request(BaseModel):
    """Request model for base64 audio transcription."""
    audio_base64: str
    language: str = "en-US"
    engine: Optional[str] = None


@router.post("/transcribe/base64", response_model=Dict[str, Any])
async def transcribe_audio_base64(
    request: TranscribeBase64Request,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Transcribe base64-encoded audio to text.
    
    Alternative to file upload for WebSocket or embedded audio.
    
    Args:
        request: TranscribeBase64Request with audio_base64, language, engine
        current_user: Authenticated user
        
    Returns:
        Transcription result
    """
    try:
        # Decode base64
        audio_data = base64.b64decode(request.audio_base64)
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio data"
            )
        
        # Transcribe
        result = await stt_service.transcribe(
            audio_data=audio_data,
            language=request.language,
            engine=request.engine
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get("/stt/engines")
async def list_stt_engines(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available STT engines.
    
    Returns:
        Available engines and current configuration
    """
    return {
        "engines": stt_service.list_engines(),
        "current": stt_service.get_current_engine()
    }


# ==================== TTS Endpoints ====================

@router.post("/synthesize")
async def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    language: str = "en-US",
    engine: Optional[str] = None,
    return_base64: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Synthesize text to speech using configured TTS engine.
    
    Args:
        text: Text to convert to speech
        voice: Voice name/ID (engine-specific)
        language: Language code
        engine: Optional engine override (google, custom)
        return_base64: Return base64 or raw audio bytes
        current_user: Authenticated user
        
    Returns:
        Audio data (base64 JSON or raw bytes)
    """
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is required"
            )
        
        # Synthesize
        result = await tts_service.synthesize(
            text=text,
            voice=voice,
            language=language,
            engine=engine
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        if return_base64:
            return {
                "audio_base64": result["audio_base64"],
                "content_type": result["content_type"],
                "duration_seconds": result["duration_seconds"],
                "engine": result.get("engine")
            }
        else:
            # Return raw audio
            return Response(
                content=result["audio"],
                media_type=result["content_type"],
                headers={
                    "X-Duration-Seconds": str(result["duration_seconds"]),
                    "X-Engine": result.get("engine", "unknown")
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.get("/tts/engines")
async def list_tts_engines(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available TTS engines.
    
    Returns:
        Available engines and current configuration
    """
    return {
        "engines": tts_service.list_engines(),
        "current": tts_service.get_current_engine()
    }


@router.get("/tts/voices")
async def list_voices(
    language: str = "en-US",
    engine: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available voices for TTS.
    
    Args:
        language: Language code to filter voices
        engine: Optional engine to query
        current_user: Authenticated user
        
    Returns:
        List of available voices
    """
    voices = tts_service.list_voices(language=language, engine=engine)
    return {
        "language": language,
        "engine": engine or tts_service.get_current_engine(),
        "voices": voices
    }
