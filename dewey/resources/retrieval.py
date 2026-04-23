"""Retrieval resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..client import DeweyHttpClient
from ..types import RetrievalResult


class RetrievalResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def query(
        self,
        collection_id: str,
        q: str,
        *,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Hybrid semantic + keyword search over a collection.

        :param collection_id: The collection to query.
        :param q: The natural-language query string.
        :param limit: Maximum number of results (1–50, default 10).
        :param tags: Return only docs that have ALL of these tags.
        :param any_tags: Return only docs that have ANY of these tags.
        :param metadata: Return only docs whose metadata contains all of
            these key-value pairs (JSONB containment match).
        """
        body: dict = {"q": q}
        if limit is not None:
            body["limit"] = limit
        if tags:
            body["tags"] = tags
        if any_tags:
            body["anyTags"] = any_tags
        if metadata:
            body["metadata"] = metadata
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/query",
            body=body,
        )
        return [RetrievalResult.from_dict(r) for r in data]
