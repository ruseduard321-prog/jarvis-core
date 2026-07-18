from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from datetime import datetime

from backend.core.dependencies import (
    get_memory_service,
    get_knowledge_repository,
    get_retrieval_engine,
    get_embedding_provider,
)
from backend.core.memory_models import MemoryMetadata, MemoryRecord
from backend.core.knowledge_models import KnowledgeDocument, KnowledgeChunk, KnowledgeSource, KnowledgeSourceType
from backend.core.retrieval_models import RetrievalRequest, RetrievedDocument
from backend.schemas.knowledge import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemoryQueryRequest,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentResponse,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
    RetrievalDocument,
)

router = APIRouter(tags=["knowledge", "memory"])


# ============================================================
# MEMORY ENDPOINTS
# ============================================================

@router.post("/memory", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    request: MemoryCreateRequest,
    memory_service=Depends(get_memory_service),
) -> MemoryResponse:
    """Create a new memory record."""
    try:
        metadata = MemoryMetadata(
            source=request.source,
            tags=request.tags,
            attributes=request.attributes,
        )
        record = MemoryRecord(
            id=str(uuid.uuid4()),
            record_type=request.record_type,
            content=request.content,
            metadata=metadata,
        )
        created = await memory_service.create_memory(record)
        
        return MemoryResponse(
            id=created.id,
            record_type=created.record_type,
            content=created.content,
            source=created.metadata.source,
            tags=created.metadata.tags,
            attributes=created.metadata.attributes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/memory/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    memory_service=Depends(get_memory_service),
) -> MemoryResponse:
    """Get a memory record by ID."""
    try:
        record = await memory_service.get_memory(memory_id)
        
        return MemoryResponse(
            id=record.id,
            record_type=record.record_type,
            content=record.content,
            source=record.metadata.source,
            tags=record.metadata.tags,
            attributes=record.metadata.attributes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}",
        )


@router.patch("/memory/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    memory_service=Depends(get_memory_service),
) -> MemoryResponse:
    """Update a memory record."""
    try:
        record = await memory_service.get_memory(memory_id)
        
        # Update record
        updated_record = MemoryRecord(
            id=record.id,
            record_type=record.record_type,
            content=request.content or record.content,
            metadata=MemoryMetadata(
                source=record.metadata.source,
                tags=request.tags or record.metadata.tags,
                attributes=request.attributes or record.metadata.attributes,
            ),
        )
        updated = await memory_service.update_memory(memory_id, updated_record)
        
        return MemoryResponse(
            id=updated.id,
            record_type=updated.record_type,
            content=updated.content,
            source=updated.metadata.source,
            tags=updated.metadata.tags,
            attributes=updated.metadata.attributes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    memory_service=Depends(get_memory_service),
) -> None:
    """Delete a memory record."""
    try:
        await memory_service.delete_memory(memory_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/memory/query", response_model=list[MemoryResponse])
async def query_memory(
    request: MemoryQueryRequest,
    memory_service=Depends(get_memory_service),
) -> list[MemoryResponse]:
    """Query memory records."""
    try:
        # Build query filters
        attributes = {}
        if request.tags:
            attributes["tags"] = request.tags
        if request.record_type:
            attributes["record_type"] = request.record_type
            
        results = await memory_service.query_memory(
            query=request.query or "",
            attributes=attributes,
            limit=request.limit,
        )
        
        return [
            MemoryResponse(
                id=r.id,
                record_type=r.record_type,
                content=r.content,
                source=r.metadata.source,
                tags=r.metadata.tags,
                attributes=r.metadata.attributes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# KNOWLEDGE DOCUMENT ENDPOINTS
# ============================================================

@router.post("/knowledge/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_document(
    request: KnowledgeDocumentCreateRequest,
    knowledge_repo=Depends(get_knowledge_repository),
    embedding_provider=Depends(get_embedding_provider),
) -> KnowledgeDocumentResponse:
    """Create a knowledge document."""
    try:
        source = KnowledgeSource(
            type=KnowledgeSourceType(request.source_type),
            identifier=request.source_identifier or request.title,
        )
        
        document = KnowledgeDocument(
            id=str(uuid.uuid4()),
            title=request.title,
            content=request.content,
            source=source,
            metadata=request.metadata,
        )
        
        # Create document chunks (simple chunking: split by sentences)
        chunks = []
        sentences = request.content.split(". ")
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                chunk = KnowledgeChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=sentence.strip() + ".",
                    chunk_index=i,
                )
                chunks.append(chunk)
        
        # Store document
        created = await knowledge_repo.create_document(document, chunks)
        
        return KnowledgeDocumentResponse(
            id=created.id,
            title=created.title,
            source_type=created.source.type.value,
            source_identifier=created.source.identifier,
            chunk_count=len(chunks),
            tags=request.tags,
            metadata=created.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/knowledge/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_knowledge_document(
    document_id: str,
    knowledge_repo=Depends(get_knowledge_repository),
) -> KnowledgeDocumentResponse:
    """Get a knowledge document by ID."""
    try:
        document = await knowledge_repo.get_document(document_id)
        chunks = await knowledge_repo.get_chunks(document_id)
        
        return KnowledgeDocumentResponse(
            id=document.id,
            title=document.title,
            source_type=document.source.type.value,
            source_identifier=document.source.identifier,
            chunk_count=len(chunks),
            tags=[],
            metadata=document.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.delete("/knowledge/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_document(
    document_id: str,
    knowledge_repo=Depends(get_knowledge_repository),
) -> None:
    """Delete a knowledge document."""
    try:
        await knowledge_repo.delete_document(document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# RETRIEVAL / RAG ENDPOINTS
# ============================================================

@router.post("/retrieval/query", response_model=RetrievalQueryResponse)
async def retrieve_context(
    request: RetrievalQueryRequest,
    retrieval_engine=Depends(get_retrieval_engine),
    embedding_provider=Depends(get_embedding_provider),
) -> RetrievalQueryResponse:
    """Retrieve context for RAG using semantic search."""
    try:
        # Create retrieval request
        retrieval_request = RetrievalRequest(
            query=request.query,
            namespace=request.namespace,
            tags=request.tags,
            limit=request.limit,
        )
        
        # Execute retrieval
        result = await retrieval_engine.execute(retrieval_request)
        
        # Convert to response format
        documents = [
            RetrievalDocument(
                id=doc.id,
                title=doc.source,
                content=doc.content,
                source=doc.source,
                tags=doc.metadata.get("tags", []) if doc.metadata else [],
                similarity_score=doc.similarity_score,
            )
            for doc in result.documents
        ]
        
        return RetrievalQueryResponse(
            query=request.query,
            documents=documents,
            total_count=result.total_count,
            augmented_prompt=f"Based on retrieved documents: {request.query}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
