"""Retrieval resource."""

from __future__ import annotations

from typing import List, Optional

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
    ) -> List[RetrievalResult]:
        """
        Hybrid semantic + keyword search over a collection.

        :param collection_id: The collection to query.
        :param q: The natural-language query string.
        :param limit: Maximum number of results (1–50, default 10).
        """
        body: dict = {"q": q}
        if limit is not None:
            body["limit"] = limit
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/query",
            body=body,
        )
        return [RetrievalResult.from_dict(r) for r in data]
