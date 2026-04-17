"""Duplicates resource — fuzzy document deduplication.

Identifies near-duplicate documents within a collection by measuring how much
content they share and marks one member of each cluster as canonical.
Non-canonical documents are excluded from retrieval and contradiction
detection.

Must be enabled per-collection via
``client.collections.update(id, enable_deduplication=True)``.
"""

from __future__ import annotations

from typing import Optional

from ..client import DeweyHttpClient
from ..types import (
    DuplicateDetectResult,
    DuplicateGroupList,
    DuplicateRun,
)


class DuplicatesResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def detect(self, collection_id: str) -> DuplicateDetectResult:
        """
        Trigger an asynchronous deduplication run across every ready document
        in the collection. Poll progress with :meth:`get_latest_run`.

        Requires ``enable_deduplication`` to be set on the collection. Raises
        :class:`DeweyError` with status 409 if a dedup run is already in flight.
        """
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/duplicates/detect",
        )
        return DuplicateDetectResult.from_dict(data)

    def get_latest_run(self, collection_id: str) -> DuplicateRun:
        """Get the status and stats of the latest deduplication run."""
        data = self._client.request(
            "GET",
            f"/collections/{collection_id}/duplicates/runs/latest",
        )
        return DuplicateRun.from_dict(data)

    def list(
        self,
        collection_id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DuplicateGroupList:
        """
        List duplicate groups in the collection with their members.

        :param limit: Maximum results to return (1–100). Default 50.
        :param offset: Pagination offset. Default 0.
        """
        params: list[str] = []
        if limit is not None:
            params.append(f"limit={limit}")
        if offset is not None:
            params.append(f"offset={offset}")
        qs = "&".join(params)
        path = f"/collections/{collection_id}/duplicates"
        if qs:
            path += f"?{qs}"
        data = self._client.request("GET", path)
        return DuplicateGroupList.from_dict(data)

    def promote_canonical(
        self,
        collection_id: str,
        group_id: str,
        canonical_document_id: str,
    ) -> dict:
        """
        Promote a different member of the group to canonical. The previous
        canonical becomes a near_duplicate. Coverage percentages are cleared
        since they describe the old pairing.
        """
        return self._client.request(
            "PATCH",
            f"/collections/{collection_id}/duplicates/{group_id}",
            body={"canonicalDocumentId": canonical_document_id},
        )

    def disband(self, collection_id: str, group_id: str) -> dict:
        """
        Disband a duplicate group. All former members rejoin retrieval as
        distinct documents with no group membership or canonical relationship.
        """
        return self._client.request(
            "DELETE",
            f"/collections/{collection_id}/duplicates/{group_id}",
        )
