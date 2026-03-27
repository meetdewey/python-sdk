"""Collections resource."""

from __future__ import annotations

from typing import List, Literal, Optional

from ..client import DeweyHttpClient
from ..types import Collection


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
    ) -> Collection:
        """Update a collection."""
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
        data = self._client.request("PATCH", f"/collections/{collection_id}", body=body)
        return Collection.from_dict(data)

    def delete(self, collection_id: str) -> None:
        """Delete a collection (soft delete). Returns None on success."""
        self._client.request("DELETE", f"/collections/{collection_id}")
