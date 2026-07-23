from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Any

from backend.core.normalized_document import NormalizedDocument


class ToolContentProcessingService:
    """Shared content processing helpers for reader/search tools."""

    _WS_RE = re.compile(r"[ \t]+")
    _BLANK_RE = re.compile(r"\n{3,}")

    def normalize_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = self._WS_RE.sub(" ", normalized)
        normalized = self._BLANK_RE.sub("\n\n", normalized)
        return normalized.strip()

    def extract_html_metadata(self, html: str, url: str) -> dict[str, Any]:
        title = self._extract_first(html, r"<title[^>]*>(.*?)</title>")
        publish_date = self._extract_publish_date(html)
        return {
            "title": unescape(title).strip() if title else "",
            "url": url,
            "publish_date": publish_date,
        }

    def clean_html_to_text(self, html: str) -> str:
        body = self._extract_first(html, r"<body[^>]*>([\s\S]*?)</body>") or html
        body = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.IGNORECASE)
        body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.IGNORECASE)
        body = re.sub(r"<nav[\s\S]*?</nav>", " ", body, flags=re.IGNORECASE)
        body = re.sub(r"<aside[\s\S]*?</aside>", " ", body, flags=re.IGNORECASE)
        body = re.sub(r"<footer[\s\S]*?</footer>", " ", body, flags=re.IGNORECASE)

        # Preserve block structure for headings and paragraphs before stripping tags.
        body = re.sub(r"</h[1-6]>", "\n\n", body, flags=re.IGNORECASE)
        body = re.sub(r"<h[1-6][^>]*>", "\n\n", body, flags=re.IGNORECASE)
        body = re.sub(r"</p>", "\n\n", body, flags=re.IGNORECASE)
        body = re.sub(r"<p[^>]*>", "", body, flags=re.IGNORECASE)
        body = re.sub(r"<br\s*/?>", "\n", body, flags=re.IGNORECASE)

        body = re.sub(r"<[^>]+>", " ", body)
        body = unescape(body)
        return self.normalize_text(body)

    def parse_markdown_preserving_structure(self, markdown_text: str) -> str:
        lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        out: list[str] = []
        in_code = False

        for line in lines:
            stripped = line.rstrip()
            if stripped.startswith("```"):
                in_code = not in_code
                out.append(stripped)
                continue

            if in_code:
                out.append(stripped)
                continue

            if stripped.startswith("#") or stripped.startswith("-") or re.match(r"^\\d+\\.\\s", stripped):
                out.append(stripped)
            else:
                out.append(self._WS_RE.sub(" ", stripped).strip())

        return self.normalize_text("\n".join(out))

    def chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")

        chunks: list[str] = []
        i = 0
        while i < len(text):
            chunks.append(text[i : i + chunk_size])
            i += chunk_size - overlap
        return [chunk for chunk in chunks if chunk.strip()]

    def extract_pdf_text(self, raw: bytes) -> tuple[str, dict[str, Any]]:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            raise RuntimeError("PDF reader dependency missing: install 'pypdf'.")

        reader = PdfReader(BytesIO(raw))
        page_texts: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            normalized = self.normalize_text(extracted)
            page_texts.append(f"# Page {index}\n\n{normalized}")

        return "\n\n".join(page_texts).strip(), {"pages": len(reader.pages)}

    def build_document(
        self,
        *,
        content: str,
        source_meta: dict[str, Any],
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
        language: str | None = None,
        chunk_size: int = 1200,
        chunk_overlap: int = 120,
    ) -> NormalizedDocument:
        merged_metadata = {**source_meta, **(metadata or {})}
        source = str(source_meta.get("source", ""))
        url = source_meta.get("url")

        resolved_title = (title or "").strip() or self._derive_title(source_meta)
        resolved_language = language or self._derive_language(source_meta)
        normalized_content = self.normalize_text(content)

        return NormalizedDocument(
            title=resolved_title,
            content=normalized_content,
            metadata=merged_metadata,
            source=source,
            url=str(url) if url else None,
            language=resolved_language,
            chunks=self.chunk_text(normalized_content, chunk_size=chunk_size, overlap=chunk_overlap),
        )

    def _extract_first(self, content: str, pattern: str) -> str | None:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1)

    def _extract_publish_date(self, html: str) -> str | None:
        candidates = [
            self._extract_first(html, r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\'](.*?)["\']'),
            self._extract_first(html, r'<meta[^>]+name=["\']pubdate["\'][^>]+content=["\'](.*?)["\']'),
            self._extract_first(html, r'<time[^>]+datetime=["\'](.*?)["\']'),
        ]

        for candidate in candidates:
            if not candidate:
                continue
            try:
                datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                return candidate
            except ValueError:
                continue
        return None

    def _derive_title(self, source_meta: dict[str, Any]) -> str:
        provided_title = str(source_meta.get("title", "")).strip()
        if provided_title:
            return provided_title

        url = str(source_meta.get("url", "")).strip()
        if url:
            return url

        path = str(source_meta.get("path", "")).strip()
        if path:
            return Path(path).name

        return "Untitled Document"

    def _derive_language(self, source_meta: dict[str, Any]) -> str:
        path = str(source_meta.get("path", "")).lower()
        content_type = str(source_meta.get("content_type", "")).lower()

        if path.endswith(".md"):
            return "markdown"
        if path.endswith(".txt"):
            return "text"
        if path.endswith(".pdf") or "application/pdf" in content_type:
            return "pdf"
        if "text/html" in content_type:
            return "html"
        if "text/markdown" in content_type:
            return "markdown"

        return "text"
