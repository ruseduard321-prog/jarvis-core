from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
import uuid
from datetime import datetime

from backend.core.dependencies import (
    get_document_ingestion_engine,
    get_knowledge_repository,
    get_embedding_provider,
    get_vector_service,
)
from backend.core.document_ingestion import DocumentFormat
from backend.core.knowledge_models import KnowledgeSource, KnowledgeSourceType
from backend.schemas.knowledge import DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents", "ingestion"])


# ============================================================
# DOCUMENT UPLOAD & INGESTION ENDPOINTS
# ============================================================

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    namespace: str = Form(default="default"),
    tags: str = Form(default=""),
    chunk_size: int = Form(default=1000),
    chunk_overlap: int = Form(default=100),
    ingestion_engine=Depends(get_document_ingestion_engine),
    knowledge_repo=Depends(get_knowledge_repository),
    vector_service=Depends(get_vector_service),
    embedding_provider=Depends(get_embedding_provider),
) -> DocumentUploadResponse:
    """Upload and ingest a document."""
    try:
        # Read file content
        content = await file.read()
        
        # Determine format from filename
        filename = file.filename or "document"
        if filename.endswith(".txt"):
            format = DocumentFormat.TEXT
        elif filename.endswith(".md"):
            format = DocumentFormat.MARKDOWN
        elif filename.endswith(".pdf"):
            format = DocumentFormat.PDF
        elif filename.endswith(".docx"):
            format = DocumentFormat.DOCX
        else:
            format = DocumentFormat.TEXT
        
        # Use provided title or derive from filename
        doc_title = title or filename.rsplit(".", 1)[0]
        
        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Ingest document
        job, chunks = await ingestion_engine.ingest(
            file_content=content,
            title=doc_title,
            format=format,
            namespace=namespace,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata={"tags": tag_list, "filename": filename},
        )
        
        # Create knowledge document
        source = KnowledgeSource(
            type=KnowledgeSourceType.DOCUMENT,
            identifier=filename,
        )

        # Store in knowledge repository
        stored_doc = await knowledge_repo.create_document(
            title=doc_title,
            content="\n".join([chunk.content for chunk in chunks]),
            source=source,
            metadata={"namespace": namespace, "tags": tag_list},
        )
        for chunk in chunks:
            await knowledge_repo.create_chunk(
                document_id=stored_doc.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
            )

        # Generate embeddings and store vectors (if enabled)
        # For now, this is a placeholder
        
        return DocumentUploadResponse(
            document_id=job.document_id,
            title=doc_title,
            file_size=len(content),
            chunk_count=job.chunk_count,
            ingestion_status=job.status,
            job_id=job.id,
            created_at=job.started_at or datetime.utcnow(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/ingestion-jobs/{job_id}")
async def get_ingestion_job_status(
    job_id: str,
    ingestion_engine=Depends(get_document_ingestion_engine),
) -> dict:
    """Get ingestion job status."""
    try:
        job = ingestion_engine.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )
        
        return {
            "job_id": job.id,
            "document_id": job.document_id,
            "status": job.status,
            "format": job.format.value,
            "file_size": job.file_size,
            "chunk_count": job.chunk_count,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
