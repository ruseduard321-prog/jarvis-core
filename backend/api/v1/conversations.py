from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.core.dependencies import (
    get_conversation_engine,
    get_rag_service,
    get_event_bus_service,
)
from backend.core.conversation_models import Conversation, ConversationMessage, ConversationRole
from backend.core.rag_models import RAGContext
from backend.schemas.conversation import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatStreamEvent,
)
from pydantic import UUID4
import json
import uuid

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============================================================
# CONVERSATION ENDPOINTS
# ============================================================

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreateRequest,
    engine=Depends(get_conversation_engine),
) -> ConversationResponse:
    """Create a new conversation."""
    try:
        conversation = await engine.create_conversation(
            title=request.title,
            metadata=request.metadata,
        )
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            metadata=conversation.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    engine=Depends(get_conversation_engine),
) -> ConversationResponse:
    """Get a conversation by ID."""
    try:
        conversation = await engine.load_conversation(conversation_id)
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            metadata=conversation.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {conversation_id}",
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    engine=Depends(get_conversation_engine),
) -> ConversationResponse:
    """Update a conversation."""
    try:
        conversation = await engine.load_conversation(conversation_id)
        
        # Update metadata if provided
        if request.metadata is not None:
            metadata = {**conversation.metadata, **request.metadata}
        else:
            metadata = conversation.metadata
            
        updated = await engine.update_metadata(conversation_id, metadata)
        
        return ConversationResponse(
            id=updated.id,
            title=request.title or updated.title,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            metadata=metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    engine=Depends(get_conversation_engine),
) -> None:
    """Delete a conversation."""
    try:
        await engine.delete_conversation(conversation_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# MESSAGE ENDPOINTS
# ============================================================

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: str,
    request: MessageCreateRequest,
    engine=Depends(get_conversation_engine),
) -> MessageResponse:
    """Add a message to a conversation."""
    try:
        conversation = await engine.load_conversation(conversation_id)
        
        # Create message
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole(request.role),
            content=request.content,
            metadata=request.metadata,
        )
        
        # Append to conversation
        updated = await engine.append_message(conversation_id, message)
        
        return MessageResponse(
            id=message.id,
            conversation_id=conversation_id,
            content=message.content,
            role=message.role.value,
            created_at=message.created_at or __import__("datetime").datetime.utcnow(),
            metadata=message.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    engine=Depends(get_conversation_engine),
) -> list[MessageResponse]:
    """List messages in a conversation."""
    try:
        conversation = await engine.load_conversation(conversation_id)
        
        return [
            MessageResponse(
                id=msg.id,
                conversation_id=conversation_id,
                content=msg.content,
                role=msg.role.value,
                created_at=msg.created_at or __import__("datetime").datetime.utcnow(),
                metadata=msg.metadata,
            )
            for msg in conversation.messages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# CHAT COMPLETION ENDPOINTS
# ============================================================

@router.post("/{conversation_id}/chat", response_model=ChatCompletionResponse)
async def chat_completion(
    conversation_id: str,
    request: ChatCompletionRequest,
    engine=Depends(get_conversation_engine),
    rag_service=Depends(get_rag_service),
    event_bus=Depends(get_event_bus_service),
) -> ChatCompletionResponse:
    """Send a message and get a chat completion (non-streaming)."""
    try:
        # Prepare RAG context if requested
        rag_context_used = False
        if request.use_rag:
            try:
                rag_result = await rag_service.execute(
                    RAGContext(user_query=request.message, conversation_id=conversation_id)
                )
                rag_context_used = True
                augmented_prompt = rag_result.augmented_prompt
            except Exception:
                augmented_prompt = request.message
                rag_context_used = False
        else:
            augmented_prompt = request.message

        # Add user message to conversation
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.USER,
            content=request.message,
            metadata=request.metadata,
        )
        await engine.append_message(conversation_id, user_msg)

        # Generate assistant response
        # For now, return placeholder (future: call LLM)
        assistant_response = f"[Assistant response to: {augmented_prompt[:100]}...]"
        assistant_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.ASSISTANT,
            content=assistant_response,
            metadata={"rag_augmented": rag_context_used},
        )
        await engine.append_message(conversation_id, assistant_msg)

        # Emit event
        await event_bus.publish_event(
            "ConversationCompleted",
            payload={
                "conversation_id": conversation_id,
                "user_message_id": user_msg.id,
                "assistant_message_id": assistant_msg.id,
            },
            metadata={"conversation_id": conversation_id},
        )

        return ChatCompletionResponse(
            conversation_id=conversation_id,
            user_message_id=user_msg.id,
            assistant_message_id=assistant_msg.id,
            content=assistant_response,
            tokens_used=None,
            rag_context_used=rag_context_used,
            metadata={"rag_augmented": rag_context_used},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{conversation_id}/chat/stream")
async def chat_completion_stream(
    conversation_id: str,
    request: ChatCompletionRequest,
    engine=Depends(get_conversation_engine),
    rag_service=Depends(get_rag_service),
    event_bus=Depends(get_event_bus_service),
):
    """Send a message and stream chat completion (Server-Sent Events)."""
    
    async def event_generator():
        try:
            # Add user message
            user_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                role=ConversationRole.USER,
                content=request.message,
                metadata=request.metadata,
            )
            await engine.append_message(conversation_id, user_msg)
            
            # Start stream
            yield f"data: {json.dumps({'event': 'start', 'message_id': user_msg.id})}\n\n"
            
            # Stream tokens (placeholder)
            response_text = f"Response to: {request.message[:50]}..."
            for token in response_text.split():
                yield f"data: {json.dumps({'event': 'token', 'data': token + ' '})}\n\n"
            
            # Create and append assistant message
            assistant_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                role=ConversationRole.ASSISTANT,
                content=response_text,
                metadata={"rag_augmented": request.use_rag},
            )
            await engine.append_message(conversation_id, assistant_msg)
            
            # End stream
            yield f"data: {json.dumps({'event': 'end', 'message_id': assistant_msg.id})}\n\n"
            
            # Emit event
            await event_bus.publish_event(
                "ConversationCompleted",
                payload={
                    "conversation_id": conversation_id,
                    "user_message_id": user_msg.id,
                    "assistant_message_id": assistant_msg.id,
                },
                metadata={"conversation_id": conversation_id},
            )
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
