from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.core.dependencies import (
    get_conversation_engine,
    get_rag_service,
    get_event_bus_service,
    get_llm_provider,
    get_agent_runtime,
    get_agent_service,
    get_workflow_manager,
)
from backend.core.conversation_exceptions import ConversationNotFoundError
from backend.core.conversation_models import Conversation, ConversationMessage, ConversationRole
from backend.core.llm_models import LLMRequest, LLMMessage
from backend.core.config import settings
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
import traceback
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def _resolve_agent_id(requested_agent_id: str | None, agent_service) -> str:
    """Resolve the agent to execute a chat turn with.

    Normal chat requests must always execute through AgentRuntime. When the caller does not
    specify an agent_id, the seeded General Assistant is used automatically so the frontend is
    never required to select an agent.
    """
    if requested_agent_id:
        return requested_agent_id

    default_agent = await agent_service.get_default_agent()
    if default_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Default agent 'general' (General Assistant) is not available. Agent execution cannot proceed.",
        )
    return default_agent.id


# ============================================================
# CONVERSATION ENDPOINTS
# ============================================================

@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    engine=Depends(get_conversation_engine),
) -> list[ConversationResponse]:
    """List all conversations."""
    try:
        # Get all conversations from store
        conversations = await engine.list_conversations()
        return [
            ConversationResponse(
                id=conv.context.conversation_id,
                title=conv.context.title,
                created_at=conv.context.created_at,
                updated_at=conv.context.updated_at,
                metadata=conv.context.metadata,
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


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
            id=conversation.context.conversation_id,
            title=conversation.context.title,
            created_at=conversation.context.created_at,
            updated_at=conversation.context.updated_at,
            metadata=conversation.context.metadata,
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
            id=conversation.context.conversation_id,
            title=conversation.context.title,
            created_at=conversation.context.created_at,
            updated_at=conversation.context.updated_at,
            metadata=conversation.context.metadata,
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
            metadata = {**conversation.context.metadata, **request.metadata}
        else:
            metadata = conversation.context.metadata
            
        updated = await engine.update_metadata(conversation_id, metadata)
        
        return ConversationResponse(
            id=updated.context.conversation_id,
            title=request.title or updated.context.title,
            created_at=updated.context.created_at,
            updated_at=updated.context.updated_at,
            metadata=metadata,
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
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
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
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
            created_at=datetime.utcnow(),
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
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
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
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
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
    llm_provider=Depends(get_llm_provider),
    agent_runtime=Depends(get_agent_runtime),
    agent_service=Depends(get_agent_service),
    workflow_manager=Depends(get_workflow_manager),
) -> ChatCompletionResponse:
    """Send a message and get a chat completion (non-streaming). Always executes through
    AgentRuntime; agent_id defaults to the General Assistant when not provided. Requests
    asking for a complete production deliverable are routed to WorkflowManager instead."""
    resolved_agent_id = await _resolve_agent_id(request.agent_id, agent_service)

    try:
        workflow_plan = await workflow_manager.detect(request.message)
        if workflow_plan and workflow_plan.get("is_full_production"):
            message_id = None
            assistant_message_id = None
            content = ""
            async for event in workflow_manager.stream_execute(
                conversation_id=conversation_id,
                message=request.message,
                topic=workflow_plan["topic"],
                user_id=None,
            ):
                if event["event"] == "start":
                    message_id = event["message_id"]
                elif event["event"] == "token":
                    content += event["data"]
                elif event["event"] == "end":
                    assistant_message_id = event["message_id"]

            return ChatCompletionResponse(
                conversation_id=conversation_id,
                user_message_id=message_id or "",
                assistant_message_id=assistant_message_id or "",
                content=content.strip(),
                tokens_used=None,
                rag_context_used=False,
                metadata={"workflow": "full_production"},
            )

        runtime_result = await agent_runtime.execute(
            conversation_id=conversation_id,
            agent_id=resolved_agent_id,
            message=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )

        return ChatCompletionResponse(
            conversation_id=conversation_id,
            user_message_id=runtime_result["user_message_id"],
            assistant_message_id=runtime_result["assistant_message_id"],
            content=runtime_result["content"],
            tokens_used=None,
            rag_context_used=False,
            metadata={"agent_id": resolved_agent_id, "execution_id": runtime_result["execution_id"]},
        )

        # Legacy direct-LLM/RAG path. No longer reachable from normal requests now that
        # agent_id always resolves above; retained only as existing code, per F16 scope
        # (normal chat must always execute through AgentRuntime, never fall back silently).
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
            created_at=datetime.utcnow(),
            metadata=request.metadata,
        )
        await engine.append_message(conversation_id, user_msg)

        # Load conversation history for LLM context
        conversation = await engine.load_conversation(conversation_id)
        
        # Build LLM messages
        llm_messages = []
        
        # Add system prompt
        system_prompt = request.system_prompt or "You are a helpful AI assistant."
        llm_messages.append(LLMMessage(role="system", content=system_prompt))
        
        # Add conversation history (excluding the user message we just added)
        for msg in conversation.messages[:-1]:  # Exclude last added user message to rebuild it below
            llm_messages.append(LLMMessage(role=msg.role.value, content=msg.content))
        
        # Add current user message
        llm_messages.append(LLMMessage(role="user", content=augmented_prompt))
        
        # Build LLM request with optional parameters
        llm_request = LLMRequest(
            model=settings.default_llm_model,
            messages=llm_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider=settings.default_llm_provider,
        )
        
        # Generate assistant response via LLM
        assistant_response = ""
        async for llm_response in llm_provider.stream(llm_request):
            assistant_response = llm_response.output
        
        assistant_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.ASSISTANT,
            content=assistant_response,
            created_at=datetime.utcnow(),
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
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )




@router.get("/{conversation_id}/chat/stream")
async def chat_completion_stream(
    conversation_id: str,
    message: str,
    use_rag: bool = True,
    agent_id: str | None = None,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    engine=Depends(get_conversation_engine),
    rag_service=Depends(get_rag_service),
    event_bus=Depends(get_event_bus_service),
    llm_provider=Depends(get_llm_provider),
    agent_runtime=Depends(get_agent_runtime),
    agent_service=Depends(get_agent_service),
    workflow_manager=Depends(get_workflow_manager),
):
    """Send a message and stream chat completion (Server-Sent Events). Always executes
    through AgentRuntime; agent_id defaults to the General Assistant when not provided.
    Requests asking for a complete production deliverable (e.g. "create a video about X")
    are detected and routed to WorkflowManager instead, which runs the registered
    Workflow Engine pipeline and streams progress."""
    logger.info(f"🔵 STREAMING ENDPOINT CALLED: conversation_id={conversation_id}, message={message[:50]}, use_rag={use_rag}")

    # Resolved eagerly (outside the SSE generator) so a missing default agent surfaces as a
    # normal HTTP error response instead of an in-stream error event.
    resolved_agent_id = await _resolve_agent_id(agent_id, agent_service)
    workflow_plan = await workflow_manager.detect(message)

    async def event_generator():
        try:
            if workflow_plan and workflow_plan.get("is_full_production"):
                async for event in workflow_manager.stream_execute(
                    conversation_id=conversation_id,
                    message=message,
                    topic=workflow_plan["topic"],
                    user_id=None,
                ):
                    if event["event"] == "start":
                        yield f"event: start\ndata: {json.dumps({'message_id': event['message_id']})}\n\n"
                    elif event["event"] == "token":
                        yield f"event: token\ndata: {event['data']}\n\n"
                    elif event["event"] == "end":
                        yield f"event: end\ndata: {json.dumps({'message_id': event['message_id']})}\n\n"
                return

            if resolved_agent_id:
                async for event in agent_runtime.stream_execute(
                    conversation_id=conversation_id,
                    agent_id=resolved_agent_id,
                    message=message,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    metadata={},
                ):
                    if event["event"] == "start":
                        yield f"event: start\ndata: {json.dumps({'message_id': event['message_id']})}\n\n"
                    elif event["event"] == "token":
                        yield f"event: token\ndata: {event['data']}\n\n"
                    elif event["event"] == "end":
                        yield f"event: end\ndata: {json.dumps({'message_id': event['message_id']})}\n\n"
                return

            logger.info(f"🟢 EVENT GENERATOR STARTED")
            # Add user message
            user_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                role=ConversationRole.USER,
                content=message,
                created_at=datetime.utcnow(),
                metadata={},
            )
            logger.info(f"🟢 APPENDING USER MESSAGE")
            await engine.append_message(conversation_id, user_msg)
            logger.info(f"🟢 USER MESSAGE APPENDED")
            
            # Start stream
            logger.info(f"🟢 ABOUT TO YIELD START EVENT")
            start_event = f"event: start\ndata: {json.dumps({'message_id': user_msg.id})}\n\n"
            logger.info(f"🟢 YIELDING START EVENT")
            yield start_event
            logger.info(f"🟢 START EVENT YIELDED")
            
            # Load conversation history for LLM context
            logger.info(f"🟢 LOADING CONVERSATION HISTORY")
            try:
                conversation = await engine.load_conversation(conversation_id)
                logger.info(f"🟢 LOADED CONVERSATION WITH {len(conversation.messages)} MESSAGES")
            except Exception as e:
                logger.error(f"🔴 FAILED TO LOAD CONVERSATION: {type(e).__name__}: {e}")
                logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
                raise
            
            # Build LLM request with conversation history
            final_system_prompt = system_prompt or "You are a helpful AI assistant. Provide accurate, clear, and concise responses."
            llm_messages = [
                LLMMessage(
                    role="system",
                    content=final_system_prompt,
                ),
            ]
            
            # Add conversation history (excluding the user message we just added)
            for msg in conversation.messages[:-1]:
                llm_messages.append(
                    LLMMessage(
                        role=msg.role.value,
                        content=msg.content,
                    )
                )
            
            # Add current user message
            llm_messages.append(LLMMessage(role="user", content=message))
            
            logger.info(f"🟢 BUILDING LLM REQUEST WITH {len(llm_messages)} MESSAGES (including system prompt)")
            llm_request = LLMRequest(
                model=settings.default_llm_model,
                messages=llm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=settings.default_llm_provider,
            )
            
            # Stream from LLM provider
            logger.info(f"🟢 STARTING LLM PROVIDER STREAM")
            logger.info(f"   - llm_provider type: {type(llm_provider).__name__}")
            logger.info(f"   - llm_provider.name: {llm_provider.name}")
            logger.info(f"   - llm_provider._initialized: {getattr(llm_provider, '_initialized', 'N/A')}")
            response_tokens = []
            token_count = 0
            
            try:
                logger.info(f"🟢 CALLING llm_provider.stream()...")
                async for llm_response in llm_provider.stream(llm_request):
                    logger.info(f"🟢 RECEIVED LLM RESPONSE: model={llm_response.model}, output_length={len(llm_response.output)}")
                    
                    # Split response into tokens and yield as SSE events
                    for token in llm_response.output.split():
                        response_tokens.append(token)
                        logger.info(f"🟢 ABOUT TO YIELD TOKEN #{token_count}: {repr(token)}")
                        token_event = f"event: token\ndata: {token + ' '}\n\n"
                        yield token_event
                        logger.info(f"🟢 TOKEN #{token_count} YIELDED: {repr(token)}")
                        token_count += 1
            except Exception as e:
                logger.error(f"🔴 LLM PROVIDER STREAM FAILED: {type(e).__name__}: {str(e)}")
                logger.error(f"🔴 Full traceback:\n{traceback.format_exc()}")
                raise
            
            response_text = " ".join(response_tokens)
            logger.info(f"🟢 LLM STREAM COMPLETE - total tokens={token_count}, response_length={len(response_text)}")
            
            # Create and append assistant message
            logger.info(f"🟢 CREATING ASSISTANT MESSAGE")
            assistant_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                role=ConversationRole.ASSISTANT,
                content=response_text,
                created_at=datetime.utcnow(),
                metadata={"rag_augmented": use_rag},
            )
            logger.info(f"🟢 APPENDING ASSISTANT MESSAGE")
            await engine.append_message(conversation_id, assistant_msg)
            logger.info(f"🟢 ASSISTANT MESSAGE APPENDED")
            
            # End stream
            logger.info(f"🟢 ABOUT TO YIELD END EVENT")
            end_event = f"event: end\ndata: {json.dumps({'message_id': assistant_msg.id})}\n\n"
            yield end_event
            logger.info(f"🟢 END EVENT YIELDED")
            
            # Emit event
            logger.info(f"🟢 PUBLISHING CONVERSATION COMPLETED EVENT")
            await event_bus.publish_event(
                "ConversationCompleted",
                payload={
                    "conversation_id": conversation_id,
                    "user_message_id": user_msg.id,
                    "assistant_message_id": assistant_msg.id,
                },
                metadata={"conversation_id": conversation_id},
            )
            logger.info(f"🟢 CONVERSATION COMPLETED EVENT PUBLISHED")
        except Exception as e:
            logger.error(f"🔴 EXCEPTION IN EVENT GENERATOR: {type(e).__name__}: {str(e)}")
            logger.error(f"🔴 FULL TRACEBACK:\n{traceback.format_exc()}")
            try:
                error_event = f"event: error\ndata: {str(e)}\n\n"
                yield error_event
                logger.info(f"🔴 ERROR EVENT YIELDED")
            except Exception as yield_error:
                logger.error(f"🔴 FAILED TO YIELD ERROR EVENT: {type(yield_error).__name__}: {str(yield_error)}")
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
