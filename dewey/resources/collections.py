"""Collections resource."""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from ..client import DeweyHttpClient
from ..types import Collection, CollectionStats

# Sentinel used to distinguish "field not provided" from "set to None" for
# nullable fields like llm_model and instructions.
_UNSET: Any = object()


class CollectionsResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def create(
        self,
        name: str,
        *,
        visibility: Optional[Literal["private", "public"]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_model: Optional[str] = None,
    ) -> Collection:
        """Create a new collection."""
        body: dict = {"name": name}
        if visibility is not None:
            body["visibility"] = visibility
        if chunk_size is not None:
            body["chunkSize"] = chunk_size
        if chunk_overlap is not None:
            body["chunkOverlap"] = chunk_overlap
        if embedding_model is not None:
            body["embeddingModel"] = embedding_model
        data = self._client.request("POST", "/collections", body=body)
        return Collection.from_dict(data)

    def list(self) -> List[Collection]:
        """List all collections in the project."""
        data = self._client.request("GET", "/collections")
        return [Collection.from_dict(c) for c in data]

    def get(self, collection_id: str) -> Collection:
        """Get a collection by ID."""
        data = self._client.request("GET", f"/collections/{collection_id}")
        return Collection.from_dict(data)

    def update(
        self,
        collection_id: str,
        *,
        name: Optional[str] = None,
        visibility: Optional[Literal["private", "public"]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_model: Optional[str] = None,
        description: Optional[str] = None,
        enable_summarization: Optional[bool] = None,
        enable_captioning: Optional[bool] = None,
        llm_model: Optional[str] = _UNSET,
        instructions: Optional[str] = _UNSET,
    ) -> Collection:
        """Update a collection.

        ``llm_model`` and ``instructions`` accept ``None`` to clear the field.
        Omit the argument entirely to leave the field unchanged.
        """
        body: dict = {}
        if name is not None:
            body["name"] = name
        if visibility is not None:
            body["visibility"] = visibility
        if chunk_size is not None:
            body["chunkSize"] = chunk_size
        if chunk_overlap is not None:
            body["chunkOverlap"] = chunk_overlap
        if embedding_model is not None:
            body["embeddingModel"] = embedding_model
        if description is not None:
            body["description"] = description
        if enable_summarization is not None:
            body["enableSummarization"] = enable_summarization
        if enable_captioning is not None:
            body["enableCaptioning"] = enable_captioning
        if llm_model is not _UNSET:
            body["llmModel"] = llm_model
        if instructions is not _UNSET:
            body["instructions"] = instructions
        data = self._client.request("PATCH", f"/collections/{collection_id}", body=body)
        return Collection.from_dict(data)

    def delete(self, collection_id: str) -> None:
        """Delete a collection (soft delete). Returns None on success."""
        self._client.request("DELETE", f"/collections/{collection_id}")

    def stats(self, collection_id: str) -> CollectionStats:
        """Get document count, storage, section/chunk/claim counts, and processing status breakdown."""
        data = self._client.request("GET", f"/collections/{collection_id}/stats")
        return CollectionStats.from_dict(data)

    def recompute_summaries(self, collection_id: str) -> None:
        """Re-run AI section summarization across all documents. Returns None on success."""
        self._client.request("POST", f"/collections/{collection_id}/recompute/summaries")

    def recompute_captions(self, collection_id: str) -> None:
        """Re-run AI captioning for all images and tables across all documents. Returns None on success."""
        self._client.request("POST", f"/collections/{collection_id}/recompute/captions")

    def recompute_claims(self, collection_id: str) -> None:
        """Re-extract factual claims from all documents. Clears existing claims first. Returns None on success."""
        self._client.request("POST", f"/collections/{collection_id}/recompute/claims")
