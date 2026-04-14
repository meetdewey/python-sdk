"""Contradictions resource."""

from __future__ import annotations

from typing import Literal, Optional

from ..client import DeweyHttpClient
from ..types import (
    Contradiction,
    ContradictionDetectResult,
    ContradictionList,
    ContradictionRun,
)


class ContradictionsResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def list(
        self,
        collection_id: str,
        *,
        severity: Optional[Literal["low", "medium", "high"]] = None,
        status: Optional[Literal["active", "dismissed", "applied"]] = None,
        limit: Optional[int] = None,
    ) -> ContradictionList:
        """
        List contradictions detected in a collection.

        :param collection_id: The collection ID.
        :param severity: Filter by severity level.
        :param status: Filter by resolution status. Defaults to ``"active"``.
        :param limit: Maximum results to return (1–100).
        """
        params: list[str] = []
        if severity is not None:
            params.append(f"severity={severity}")
        if status is not None:
            params.append(f"status={status}")
        if limit is not None:
            params.append(f"limit={limit}")
        qs = "&".join(params)
        path = f"/collections/{collection_id}/contradictions"
        if qs:
            path += f"?{qs}"
        data = self._client.request("GET", path)
        return ContradictionList.from_dict(data)

    def detect(self, collection_id: str) -> ContradictionDetectResult:
        """
        Trigger an asynchronous contradiction detection run across all claims
        in a collection. Poll progress with :meth:`get_latest_run`.
        """
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/contradictions/detect",
        )
        return ContradictionDetectResult.from_dict(data)

    def get_latest_run(self, collection_id: str) -> ContradictionRun:
        """Get the status and stats of the latest contradiction detection run."""
        data = self._client.request(
            "GET",
            f"/collections/{collection_id}/contradictions/runs/latest",
        )
        return ContradictionRun.from_dict(data)

    def dismiss(
        self,
        collection_id: str,
        contradiction_id: str,
    ) -> Contradiction:
        """Dismiss a contradiction (mark as ignored)."""
        data = self._client.request(
            "PATCH",
            f"/collections/{collection_id}/contradictions/{contradiction_id}",
            body={"status": "dismissed"},
        )
        return Contradiction.from_dict(data)

    def apply_instruction(
        self,
        collection_id: str,
        contradiction_id: str,
        instruction: Optional[str] = None,
    ) -> None:
        """
        Apply a resolution instruction to a contradiction. The instruction is
        appended to the collection's research instructions automatically.

        :param instruction: Custom instruction to apply. If ``None``, the
            suggested instruction from the contradiction is used.
        """
        body: dict = {}
        if instruction is not None:
            body["instruction"] = instruction
        self._client.request(
            "POST",
            f"/collections/{collection_id}/contradictions/{contradiction_id}/apply-instruction",
            body=body,
        )
