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
from backend.core.memory_models import MemoryMetadata, MemoryQuery
from backend.core.knowledge_models import KnowledgeDocument, KnowledgeChunk, KnowledgeSource, KnowledgeSourceType
from backend.core.retrieval_models import RetrievalRequest, RetrievedDocument
from backend.schemas.knowledge import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemoryQueryRequest,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
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
        created = await memory_service.create_memory(
            record_type=request.record_type,
            content=request.content,
            metadata=metadata,
        )

        return MemoryResponse(
            id=created.id,
            record_type=created.record_type,
            content=created.content,
            source=created.metadata.source,
            tags=created.metadata.tags,
            attributes=created.metadata.attributes,
            created_at=created.created_at,
            updated_at=created.updated_at,
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
        updated_content = request.content or record.content
        updated_metadata = MemoryMetadata(
            source=record.metadata.source,
            tags=request.tags or record.metadata.tags,
            attributes=request.attributes or record.metadata.attributes,
        )
        updated = await memory_service.update_memory(memory_id, updated_content, updated_metadata)

        return MemoryResponse(
            id=updated.id,
            record_type=updated.record_type,
            content=updated.content,
            source=updated.metadata.source,
            tags=updated.metadata.tags,
            attributes=updated.metadata.attributes,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
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
        query = MemoryQuery(
            record_type=request.record_type,
            tags=request.tags,
            limit=request.limit,
        )
        result = await memory_service.query_memory(query)

        return [
            MemoryResponse(
                id=r.id,
                record_type=r.record_type,
                content=r.content,
                source=r.metadata.source,
                tags=r.metadata.tags,
                attributes=r.metadata.attributes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in result.records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/memory", response_model=list[MemoryResponse])
async def list_memory(
    limit: int = 20,
    offset: int = 0,
    memory_service=Depends(get_memory_service),
) -> list[MemoryResponse]:
    """List all memory records with pagination."""
    try:
        from backend.core.memory_models import MemoryQuery
        
        # Use list_memory for simple listing (not querying with filters)
        result = await memory_service.list_memory(limit=limit, offset=offset)
        
        return [
            MemoryResponse(
                id=r.id,
                record_type=r.record_type,
                content=r.content,
                source=r.metadata.source,
                tags=r.metadata.tags,
                attributes=r.metadata.attributes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in result.records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _document_to_response(doc) -> KnowledgeDocumentResponse:
    """Convert a repository document to a response model."""
    return KnowledgeDocumentResponse(
        id=doc.id,
        title=doc.title,
        source_type=doc.source.type.value,
        source_identifier=doc.source.identifier,
        chunk_count=len(doc.chunks) if doc.chunks else 0,
        tags=getattr(doc.metadata, 'tags', []) if hasattr(doc.metadata, 'tags') else [],
        metadata=doc.metadata if isinstance(doc.metadata, dict) else {},
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ============================================================
# KNOWLEDGE DOCUMENT ENDPOINTS
# ============================================================

@router.get("/knowledge/documents", response_model=KnowledgeDocumentListResponse)
async def list_knowledge_documents(
    knowledge_repo=Depends(get_knowledge_repository),
) -> KnowledgeDocumentListResponse:
    """List all knowledge documents."""
    try:
        documents, total_count = await knowledge_repo.list_documents()
        doc_responses = [_document_to_response(doc) for doc in documents]

        return KnowledgeDocumentListResponse(
            documents=doc_responses,
            total_count=total_count,
            timestamp=datetime.utcnow(),
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
        return _document_to_response(document)
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
        result = await retrieval_engine.retrieve(retrieval_request)
        
        # Convert to response format
        documents = [
            RetrievalDocument(
                id=doc.id,
                title=doc.source,
                content=doc.content,
                source=doc.source,
                tags=doc.metadata.get("tags", []) if doc.metadata else [],
                similarity_score=doc.score,
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
