"""
================================================================================
CHAT API ENDPOINTS FOR EVA
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from app.services.gemini_service import gemini_service
from app.services.firestore_service import firestore_service
from app.services.auth_service import auth_service
from app.models import User


# ================================================================================
# REQUEST/RESPONSE MODELS
# ================================================================================

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    response: str
    timestamp: datetime
    emotion_detected: Optional[str] = None


class ConversationInfo(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class NewConversationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=100)


class NewConversationResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime


# ================================================================================
# AUTHENTICATION HELPER (FIXED)
# ================================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    Validate the JWT token from the Header and return the current user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = auth_service.decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = await firestore_service.get_user(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ================================================================================
# ROUTER SETUP
# ================================================================================

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={401: {"description": "Not authenticated"}}
)


# ================================================================================
# ENDPOINTS (REFACTORED)
# ================================================================================

@router.post("/send", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user: User = Depends(get_current_user)
) -> ChatMessageResponse:
    """Send a message to EVA and get a response."""
    
    # Generate IDs
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    
    # Save user's message
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=message_id,
        content=request.message,
        role="user",
        timestamp=datetime.utcnow()
    )
    
    # Get response from Gemini
    response_text = await gemini_service.send_message(
        message=request.message,
        user_id=user.uid,
        conversation_id=conversation_id
    )
    
    # Save EVA's response
    response_id = f"msg_{uuid.uuid4().hex[:12]}"
    response_timestamp = datetime.utcnow()
    
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=response_id,
        content=response_text,
        role="assistant",
        timestamp=response_timestamp
    )
    
    # Update metadata
    await firestore_service.update_conversation_metadata(
        user_id=user.uid,
        conversation_id=conversation_id,
        last_message=response_text[:50]
    )
    
    return ChatMessageResponse(
        message_id=response_id,
        conversation_id=conversation_id,
        response=response_text,
        timestamp=response_timestamp
    )


@router.post("/send/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    user: User = Depends(get_current_user)
):
    """Send a message and stream EVA's response in real-time."""
    
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=f"msg_{uuid.uuid4().hex[:12]}",
        content=request.message,
        role="user",
        timestamp=datetime.utcnow()
    )
    
    async def generate():
        full_response = ""
        async for chunk in gemini_service.send_message_stream(
            message=request.message,
            user_id=user.uid,
            conversation_id=conversation_id
        ):
            full_response += chunk
            yield f"data: {json.dumps({'text': chunk, 'done': False})}\n\n"
        
        yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"
        
        await firestore_service.save_chat_message(
            user_id=user.uid,
            conversation_id=conversation_id,
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            content=full_response,
            role="assistant",
            timestamp=datetime.utcnow()
        )
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    return await firestore_service.get_chat_messages(
        user_id=user.uid,
        conversation_id=conversation_id,
        limit=limit
    )


@router.post("/new", response_model=NewConversationResponse)
async def new_conversation(
    request: NewConversationRequest = None,
    user: User = Depends(get_current_user)
) -> NewConversationResponse:
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow()
    title = request.title if request and request.title else "New Conversation"
    
    gemini_service.clear_conversation(user.uid, conversation_id)
    await firestore_service.create_conversation(
        user_id=user.uid,
        conversation_id=conversation_id,
        title=title,
        created_at=timestamp
    )
    
    return NewConversationResponse(
        conversation_id=conversation_id,
        title=title,
        created_at=timestamp
    )


@router.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations(user: User = Depends(get_current_user)) -> List[ConversationInfo]:
    conversations = await firestore_service.get_user_conversations(user.uid)
    return [
        ConversationInfo(
            conversation_id=conv["conversation_id"],
            title=conv.get("title", "Untitled"),
            created_at=conv["created_at"],
            updated_at=conv.get("updated_at", conv["created_at"]),
            message_count=conv.get("message_count", 0)
        )
        for conv in conversations
    ]


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user)
) -> Dict[str, str]:
    await firestore_service.delete_conversation(user.uid, conversation_id)
    gemini_service.clear_conversation(user.uid, conversation_id)
    return {"message": f"Conversation {conversation_id} deleted successfully"}
