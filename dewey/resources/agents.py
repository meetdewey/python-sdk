"""Agents resource (invoke saved agents — streaming and sync)."""

from __future__ import annotations

from typing import Generator

from ..client import DeweyHttpClient
from ..types import AgentInvokeResult, AgentRunEvent, agent_run_event_from_dict


class AgentsResource:
    """
    Invoke saved agents defined in the dashboard.

    Identifiers: ``org_id`` and ``project_id`` are UUIDs (not slugs).
    ``agent_slug`` is the human-readable slug shown in dashboard URLs
    (e.g. ``"qa-test"``).
    """

    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def stream(
        self,
        org_id: str,
        project_id: str,
        agent_slug: str,
        *,
        query: str,
    ) -> Generator[AgentRunEvent, None, None]:
        """
        Stream an agent run via Server-Sent Events.

        Yields ``AgentRunEvent`` objects:

        - ``AgentRunEventStarted``    — assigned ``runId``
        - ``AgentRunEventToolCall``   — a retrieval tool was invoked
        - ``AgentRunEventToolResult`` — a retrieval tool returned
        - ``AgentRunEventChunk``      — a streamed response token
        - ``AgentRunEventDone``       — run complete with sources
        - ``AgentRunEventError``      — fatal error
        - ``AgentRunEventWarning``    — non-fatal warning (e.g. timeout)

        Example::

            for event in client.agents.stream(
                org_id, project_id, "qa-test", query="What changed in 2023?"
            ):
                if event.type == "chunk":
                    print(event.content, end="", flush=True)
                elif event.type == "done":
                    print("\\nSources:", [s.filename for s in event.sources])
        """
        for raw in self._client.stream_sse(
            f"/orgs/{org_id}/projects/{project_id}/agents/{agent_slug}/invoke",
            {"query": query},
        ):
            yield agent_run_event_from_dict(raw)

    def invoke_sync(
        self,
        org_id: str,
        project_id: str,
        agent_slug: str,
        *,
        query: str,
    ) -> AgentInvokeResult:
        """
        Run an agent and wait for the buffered response.

        Same auth and pre-flight gates as :meth:`stream` (BYOK provider key,
        concurrency cap, query meter); returns once the executor terminates
        instead of streaming events.

        Example::

            result = client.agents.invoke_sync(
                org_id, project_id, "qa-test", query="What changed in 2023?"
            )
            print(result.response)
            print(len(result.sources), "sources")
        """
        raw = self._client.request(
            "POST",
            f"/orgs/{org_id}/projects/{project_id}/agents/{agent_slug}/invoke/sync",
            body={"query": query},
        )
        return AgentInvokeResult.from_dict(raw)
