"""Sections resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..client import DeweyHttpClient
from ..types import Chunk, Section


class SectionsResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def list(self, collection_id: str, document_id: str) -> List[Section]:
        """List all sections for a document."""
        data = self._client.request("GET", f"/documents/{document_id}/sections")
        return [Section.from_dict(s) for s in data]

    def get(self, section_id: str) -> Section:
        """Get a section by ID (includes content slice from Markdown)."""
        data = self._client.request("GET", f"/sections/{section_id}")
        return Section.from_dict(data)

    def get_chunks(self, section_id: str) -> List[Chunk]:
        """Get all chunks for a section."""
        data = self._client.request("GET", f"/sections/{section_id}/chunks")
        return [Chunk.from_dict(c) for c in data]

    def scan(
        self,
        collection_id: str,
        query: str,
        *,
        top_k: Optional[int] = None,
        tags: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full-text section scan — returns a ranked list of section matches.

        Returns a dict with key ``results``, each item containing ``score``,
        ``section``, and ``document``.
        """
        body: dict = {"query": query}
        if top_k is not None:
            body["top_k"] = top_k
        if tags is not None:
            body["tags"] = tags
        if any_tags is not None:
            body["anyTags"] = any_tags
        if metadata is not None:
            body["metadata"] = metadata
        return self._client.request(
            "POST",
            f"/collections/{collection_id}/sections/scan",
            body=body,
        )
