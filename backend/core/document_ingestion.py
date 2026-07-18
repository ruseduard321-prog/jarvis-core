from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator
import uuid
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentFormat(str, Enum):
    """Supported document formats."""
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    JSON = "json"


@dataclass(frozen=True)
class DocumentChunk:
    """A chunk of a document after parsing and chunking."""
    
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict[str, Any]
    tokens: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    """A parsed document ready for chunking."""
    
    id: str
    title: str
    content: str
    format: DocumentFormat
    metadata: dict[str, Any]
    parsed_at: datetime


@dataclass(frozen=True)
class IngestionJob:
    """A document ingestion job."""
    
    id: str
    document_id: str
    status: str  # pending, processing, completed, failed
    format: DocumentFormat
    file_size: int
    chunk_count: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = None


# ============================================================
# PARSER ABSTRACTION
# ============================================================

class DocumentParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    async def parse(self, content: bytes, title: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse raw document content into structured text."""
        pass
    
    @abstractmethod
    def supports_format(self, format: DocumentFormat) -> bool:
        """Check if parser supports the given format."""
        pass


class TextDocumentParser(DocumentParser):
    """Parser for plain text documents."""
    
    async def parse(self, content: bytes, title: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse text document."""
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(
            id=str(uuid.uuid4()),
            title=title,
            content=text,
            format=DocumentFormat.TEXT,
            metadata=metadata,
            parsed_at=datetime.utcnow(),
        )
    
    def supports_format(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.TEXT


class MarkdownDocumentParser(DocumentParser):
    """Parser for Markdown documents."""
    
    async def parse(self, content: bytes, title: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse Markdown document."""
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(
            id=str(uuid.uuid4()),
            title=title,
            content=text,
            format=DocumentFormat.MARKDOWN,
            metadata=metadata,
            parsed_at=datetime.utcnow(),
        )
    
    def supports_format(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.MARKDOWN


# Note: PDF and DOCX parsing requires additional dependencies (pypdf, python-docx)
# For now, we'll create placeholder parsers that treat them as text


class PDFDocumentParser(DocumentParser):
    """Parser for PDF documents."""
    
    async def parse(self, content: bytes, title: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse PDF document (placeholder)."""
        # TODO: Implement PDF parsing with pypdf library
        text = f"[PDF Content: {title}]\n\nPDF parsing not yet implemented."
        return ParsedDocument(
            id=str(uuid.uuid4()),
            title=title,
            content=text,
            format=DocumentFormat.PDF,
            metadata=metadata,
            parsed_at=datetime.utcnow(),
        )
    
    def supports_format(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.PDF


class DocxDocumentParser(DocumentParser):
    """Parser for DOCX documents."""
    
    async def parse(self, content: bytes, title: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse DOCX document (placeholder)."""
        # TODO: Implement DOCX parsing with python-docx library
        text = f"[DOCX Content: {title}]\n\nDOCX parsing not yet implemented."
        return ParsedDocument(
            id=str(uuid.uuid4()),
            title=title,
            content=text,
            format=DocumentFormat.DOCX,
            metadata=metadata,
            parsed_at=datetime.utcnow(),
        )
    
    def supports_format(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.DOCX


# ============================================================
# CHUNKING STRATEGY
# ============================================================

class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    async def chunk(self, document: ParsedDocument, chunk_size: int, overlap: int) -> list[DocumentChunk]:
        """Split document into chunks."""
        pass


class SentenceChunkingStrategy(ChunkingStrategy):
    """Chunks document by sentences."""
    
    async def chunk(self, document: ParsedDocument, chunk_size: int, overlap: int) -> list[DocumentChunk]:
        """Split document into sentence-based chunks."""
        # Simple sentence splitting (in production, use NLTK or spaCy)
        sentences = document.content.split(". ")
        
        chunks: list[DocumentChunk] = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Save chunk
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        metadata={"source": document.title},
                    )
                )
                chunk_index += 1
                
                # Create overlap
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
            
            current_chunk += sentence + ". "
        
        # Save final chunk
        if current_chunk.strip():
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={"source": document.title},
                )
            )
        
        return chunks


class CharacterChunkingStrategy(ChunkingStrategy):
    """Chunks document by character count."""
    
    async def chunk(self, document: ParsedDocument, chunk_size: int, overlap: int) -> list[DocumentChunk]:
        """Split document into character-based chunks."""
        content = document.content
        chunks: list[DocumentChunk] = []
        
        i = 0
        chunk_index = 0
        
        while i < len(content):
            # Get chunk of size chunk_size
            chunk_text = content[i : i + chunk_size]
            
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    metadata={"source": document.title},
                )
            )
            
            # Move forward, accounting for overlap
            i += chunk_size - overlap
            chunk_index += 1
        
        return chunks


# ============================================================
# INGESTION ENGINE
# ============================================================

class DocumentIngestionEngine:
    """Main document ingestion engine."""
    
    def __init__(self):
        """Initialize ingestion engine."""
        self.parsers: dict[DocumentFormat, DocumentParser] = {
            DocumentFormat.TEXT: TextDocumentParser(),
            DocumentFormat.MARKDOWN: MarkdownDocumentParser(),
            DocumentFormat.PDF: PDFDocumentParser(),
            DocumentFormat.DOCX: DocxDocumentParser(),
        }
        self.chunking_strategy = SentenceChunkingStrategy()
        self.jobs: dict[str, IngestionJob] = {}
    
    def register_parser(self, format: DocumentFormat, parser: DocumentParser) -> None:
        """Register a parser for a document format."""
        self.parsers[format] = parser
        logger.info(f"Registered parser for format: {format.value}")
    
    async def ingest(
        self,
        file_content: bytes,
        title: str,
        format: DocumentFormat,
        namespace: str = "default",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[IngestionJob, list[DocumentChunk]]:
        """Ingest a document and return chunks."""
        
        metadata = metadata or {}
        document_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Create job
        job = IngestionJob(
            id=job_id,
            document_id=document_id,
            status="processing",
            format=format,
            file_size=len(file_content),
            started_at=datetime.utcnow(),
            metadata={**metadata, "namespace": namespace},
        )
        self.jobs[job_id] = job
        
        try:
            # Parse document
            if format not in self.parsers:
                raise ValueError(f"No parser registered for format: {format.value}")
            
            parser = self.parsers[format]
            parsed_doc = await parser.parse(file_content, title, metadata)
            logger.info(f"Parsed document: {title} ({format.value})")
            
            # Chunk document
            chunks = await self.chunking_strategy.chunk(parsed_doc, chunk_size, chunk_overlap)
            logger.info(f"Created {len(chunks)} chunks from document: {title}")
            
            # Update job
            job = IngestionJob(
                id=job_id,
                document_id=document_id,
                status="completed",
                format=format,
                file_size=len(file_content),
                chunk_count=len(chunks),
                completed_at=datetime.utcnow(),
                started_at=job.started_at,
                metadata=job.metadata,
            )
            self.jobs[job_id] = job
            
            return job, chunks
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            
            # Update job with error
            job = IngestionJob(
                id=job_id,
                document_id=document_id,
                status="failed",
                format=format,
                file_size=len(file_content),
                error_message=str(e),
                completed_at=datetime.utcnow(),
                started_at=job.started_at,
                metadata=job.metadata,
            )
            self.jobs[job_id] = job
            
            raise
    
    def get_job(self, job_id: str) -> IngestionJob | None:
        """Get ingestion job status."""
        return self.jobs.get(job_id)
