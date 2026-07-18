from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================
# MEMORY SCHEMAS
# ============================================================

class MemoryCreateRequest(BaseModel):
    """Request to create a memory record."""

    record_type: str = Field(description="Type of memory (FACT, REASONING, CONTEXT, etc.)")
    content: str = Field(description="Memory content")
    source: str | None = Field(None, description="Source of the memory")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Additional attributes")

    class Config:
        json_schema_extra = {
            "example": {
                "record_type": "FACT",
                "content": "Project deadline is Q4 2026",
                "source": "project_doc",
                "tags": ["project", "deadline"],
                "attributes": {"priority": "high"},
            }
        }


class MemoryUpdateRequest(BaseModel):
    """Request to update a memory record."""

    content: str | None = Field(None, description="Updated content")
    tags: list[str] | None = Field(None, description="Updated tags")
    attributes: dict[str, Any] | None = Field(None, description="Updated attributes")


class MemoryResponse(BaseModel):
    """Response for a memory record."""

    id: str = Field(description="Memory ID")
    record_type: str = Field(description="Memory type")
    content: str = Field(description="Memory content")
    source: str | None = Field(None, description="Memory source")
    tags: list[str] = Field(default_factory=list, description="Tags")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Attributes")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "mem_abc123",
                "record_type": "FACT",
                "content": "Project deadline is Q4 2026",
                "source": "project_doc",
                "tags": ["project", "deadline"],
                "attributes": {"priority": "high"},
                "created_at": "2026-07-18T10:00:00Z",
                "updated_at": "2026-07-18T10:00:00Z",
            }
        }


class MemoryQueryRequest(BaseModel):
    """Request to query memory records."""

    query: str | None = Field(None, description="Search query")
    tags: list[str] | None = Field(None, description="Filter by tags")
    record_type: str | None = Field(None, description="Filter by type")
    limit: int = Field(default=10, description="Max results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "deadline",
                "tags": ["project"],
                "record_type": "FACT",
                "limit": 10,
            }
        }


# ============================================================
# KNOWLEDGE SCHEMAS
# ============================================================

class KnowledgeDocumentCreateRequest(BaseModel):
    """Request to create a knowledge document."""

    title: str = Field(description="Document title")
    content: str = Field(description="Document content")
    source_type: str = Field(description="Source type (DOCUMENT, WEBSITE, CONVERSATION, etc.)")
    source_identifier: str | None = Field(None, description="Source identifier (URL, file path, etc.)")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Project Requirements",
                "content": "The project requires...",
                "source_type": "DOCUMENT",
                "source_identifier": "docs/requirements.md",
                "tags": ["project", "requirements"],
                "metadata": {"version": "1.0"},
            }
        }


class KnowledgeDocumentResponse(BaseModel):
    """Response for a knowledge document."""

    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    source_type: str = Field(description="Source type")
    source_identifier: str | None = Field(None, description="Source identifier")
    chunk_count: int = Field(description="Number of chunks")
    tags: list[str] = Field(default_factory=list, description="Tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "kdoc_xyz789",
                "title": "Project Requirements",
                "source_type": "DOCUMENT",
                "source_identifier": "docs/requirements.md",
                "chunk_count": 5,
                "tags": ["project", "requirements"],
                "metadata": {"version": "1.0"},
                "created_at": "2026-07-18T10:00:00Z",
                "updated_at": "2026-07-18T10:00:00Z",
            }
        }


# ============================================================
# DOCUMENT INGESTION SCHEMAS
# ============================================================

class DocumentUploadRequest(BaseModel):
    """Request to upload and ingest a document."""

    title: str | None = Field(None, description="Document title (inferred from filename if not provided)")
    namespace: str = Field(description="Namespace for document organization")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    chunk_size: int = Field(default=1000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=100, description="Chunk overlap in characters")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Quarterly Report Q3",
                "namespace": "reports",
                "tags": ["report", "q3"],
                "chunk_size": 1000,
                "chunk_overlap": 100,
                "metadata": {"quarter": "Q3", "year": 2026},
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    document_id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    file_size: int = Field(description="File size in bytes")
    chunk_count: int = Field(description="Number of chunks created")
    ingestion_status: str = Field(description="Status (pending, in_progress, completed, failed)")
    job_id: str | None = Field(None, description="Background job ID if async")
    created_at: datetime = Field(description="Upload timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "title": "Quarterly Report Q3",
                "file_size": 25000,
                "chunk_count": 15,
                "ingestion_status": "in_progress",
                "job_id": "job_456",
                "created_at": "2026-07-18T10:00:00Z",
            }
        }


# ============================================================
# VECTOR SCHEMAS
# ============================================================

class VectorQueryRequest(BaseModel):
    """Request to query vectors."""

    query_vector: list[float] = Field(description="Query vector (embedding)")
    namespace: str | None = Field(None, description="Namespace filter")
    tags: list[str] | None = Field(None, description="Tag filters")
    limit: int = Field(default=10, description="Max results")
    threshold: float | None = Field(None, description="Similarity threshold")

    class Config:
        json_schema_extra = {
            "example": {
                "query_vector": [0.1, 0.2, -0.3],
                "namespace": "documents",
                "tags": ["important"],
                "limit": 10,
                "threshold": 0.7,
            }
        }


class VectorResponse(BaseModel):
    """Response for a vector record."""

    id: str = Field(description="Vector ID")
    vector: list[float] = Field(description="Vector data (embedding)")
    namespace: str | None = Field(None, description="Namespace")
    tags: list[str] = Field(default_factory=list, description="Tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")
    created_at: datetime = Field(description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "vec_abc123",
                "vector": [0.1, 0.2, -0.3],
                "namespace": "documents",
                "tags": ["section_1"],
                "metadata": {"document_id": "doc_123"},
                "created_at": "2026-07-18T10:00:00Z",
            }
        }


# ============================================================
# RETRIEVAL SCHEMAS
# ============================================================

class RetrievalQueryRequest(BaseModel):
    """Request for retrieval-augmented generation context."""

    query: str = Field(description="Query text")
    namespace: str | None = Field(None, description="Namespace filter")
    tags: list[str] | None = Field(None, description="Tag filters")
    limit: int = Field(default=5, description="Max documents to retrieve")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the project milestones?",
                "namespace": "documents",
                "tags": ["project"],
                "limit": 5,
            }
        }


class RetrievalDocument(BaseModel):
    """Document returned by retrieval."""

    id: str = Field(description="Document ID")
    title: str | None = Field(None, description="Document title")
    content: str = Field(description="Document snippet")
    source: str | None = Field(None, description="Document source")
    tags: list[str] = Field(default_factory=list, description="Tags")
    similarity_score: float | None = Field(None, description="Similarity score 0-1")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123",
                "title": "Project Overview",
                "content": "The project milestones are...",
                "source": "docs/overview.md",
                "tags": ["project"],
                "similarity_score": 0.92,
            }
        }


class RetrievalQueryResponse(BaseModel):
    """Response for retrieval query."""

    query: str = Field(description="Original query")
    documents: list[RetrievalDocument] = Field(description="Retrieved documents")
    total_count: int = Field(description="Total documents retrieved")
    augmented_prompt: str | None = Field(None, description="RAG-augmented prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the project milestones?",
                "documents": [],
                "total_count": 0,
                "augmented_prompt": "Based on the documents: ...",
            }
        }
