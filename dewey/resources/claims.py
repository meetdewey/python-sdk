"""Claims resource."""

from __future__ import annotations

from typing import Generator, Optional

from ..client import DeweyHttpClient
from ..types import ClaimMapItem, DocumentClaims


class ClaimsResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def map_stream(
        self,
        collection_id: str,
    ) -> Generator[dict, None, None]:
        """
        Stream the claim map for a collection via SSE.

        Yields raw event dicts as they arrive. Check ``event["type"]``:

        - ``"progress"`` — ``{ "type": "progress", "pct": float }``
        - ``"done"``     — ``{ "type": "done", "total": int, "claims": [...] }``
        - ``"error"``    — ``{ "type": "error", "message": str }``

        For typed claim objects from the ``done`` event::

            for event in client.claims.map_stream(collection_id):
                if event["type"] == "done":
                    claims = [ClaimMapItem.from_dict(c) for c in event["claims"]]
        """
        yield from self._client.stream_sse_get(
            f"/collections/{collection_id}/claims/map"
        )

    def list_by_document(
        self,
        document_id: str,
        *,
        min_importance: Optional[int] = None,
    ) -> DocumentClaims:
        """
        List claims extracted from a specific document.

        :param document_id: The document ID.
        :param min_importance: Minimum importance score (1–5). Defaults to 1.
        """
        path = f"/documents/{document_id}/claims"
        if min_importance is not None:
            path += f"?minImportance={min_importance}"
        data = self._client.request("GET", path)
        return DocumentClaims.from_dict(data)
