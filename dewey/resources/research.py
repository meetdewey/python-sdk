"""Research resource (SSE streaming and buffered query)."""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Literal, Optional

from ..client import DeweyHttpClient
from ..types import ResearchEvent, ResearchResult, research_event_from_dict

ResearchDepth = Literal["quick", "balanced", "deep", "exhaustive"]


class ResearchResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def stream(
        self,
        collection_id: str,
        q: str,
        *,
        depth: ResearchDepth = "balanced",
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[ResearchEvent, None, None]:
        """
        Stream a research session using Server-Sent Events.

        Yields ``ResearchEvent`` objects:

        - ``ResearchEventToolCall`` — a retrieval tool was invoked
        - ``ResearchEventChunk``    — a streamed response token
        - ``ResearchEventDone``     — session complete with sources
        - ``ResearchEventError``    — an error occurred

        Example::

            for event in client.research.stream(col_id, "What is X?"):
                if event.type == "chunk":
                    print(event.content, end="", flush=True)
                elif event.type == "done":
                    print("\\nSources:", event.sources)
        """
        body: dict = {"q": q, "depth": depth}
        if model is not None:
            body["model"] = model
        if tags is not None:
            body["tags"] = tags
        if any_tags is not None:
            body["anyTags"] = any_tags
        if metadata is not None:
            body["metadata"] = metadata

        for raw in self._client.stream_sse(
            f"/collections/{collection_id}/research", body
        ):
            yield research_event_from_dict(raw)

    def research_sync(
        self,
        collection_id: str,
        q: str,
        *,
        depth: ResearchDepth = "balanced",
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ResearchResult:
        """
        Run a research query and return the complete answer as a single response.
        Useful in environments that cannot consume Server-Sent Events.

        Example::

            result = client.research.research_sync(col_id, "What is X?")
            print(result.answer)
            print(result.sources)
        """
        body: dict = {"q": q, "depth": depth}
        if model is not None:
            body["model"] = model
        if tags is not None:
            body["tags"] = tags
        if any_tags is not None:
            body["anyTags"] = any_tags
        if metadata is not None:
            body["metadata"] = metadata

        raw = self._client.request(
            "POST", f"/collections/{collection_id}/research/sync", body=body
        )
        return ResearchResult.from_dict(raw)
