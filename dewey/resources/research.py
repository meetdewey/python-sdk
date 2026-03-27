"""Research resource (SSE streaming)."""

from __future__ import annotations

from typing import Generator, Literal, Optional

from ..client import DeweyHttpClient
from ..types import ResearchEvent, research_event_from_dict

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

        for raw in self._client.stream_sse(
            f"/collections/{collection_id}/research", body
        ):
            yield research_event_from_dict(raw)
