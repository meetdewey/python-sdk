"""Tests for AgentsResource."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from dewey.client import DeweyHttpClient
from dewey.resources.agents import AgentsResource
from dewey.types import (
    AgentInvokeResult,
    AgentRunEventChunk,
    AgentRunEventDone,
    AgentRunEventStarted,
)

ORG = "org-uuid-1"
PROJECT = "proj-uuid-2"
AGENT = "qa-test"


SOURCE = {
    "chunkId": "c1",
    "sectionId": "s1",
    "sectionTitle": "Methods",
    "sectionLevel": 2,
    "documentId": "d1",
    "filename": "paper.pdf",
    "score": 0.83,
    "collectionId": "col-1",
    "collectionName": "Polio",
}

INVOKE_RESULT = {
    "runId": "run-1",
    "response": "Polio cases dropped [1].",
    "sources": [SOURCE],
    "status": "succeeded",
}


def make_resource() -> AgentsResource:
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return AgentsResource(client)


def mock_urlopen_json(body, status=200):
    raw = json.dumps(body).encode()
    resp = MagicMock()
    resp.status = status
    resp.headers.get = lambda k, d="": "application/json" if k == "Content-Type" else d
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=resp)


def mock_sse_urlopen(events: list[dict]):
    """Patch urlopen to return a streaming SSE response."""
    sse_body = b""
    for event in events:
        sse_body += f"data: {json.dumps(event)}\n\n".encode()

    resp = MagicMock()
    read_results = iter([sse_body, b""])
    resp.read = MagicMock(side_effect=lambda n: next(read_results))
    resp.close = MagicMock()
    return patch("urllib.request.urlopen", return_value=resp)


class TestInvokeSync:
    def test_posts_to_invoke_sync_url(self):
        with mock_urlopen_json(INVOKE_RESULT) as mock_open:
            make_resource().invoke_sync(ORG, PROJECT, AGENT, query="Why?")
            req = mock_open.call_args[0][0]
        assert req.full_url == (
            "https://api.example.com/orgs/org-uuid-1/projects/proj-uuid-2/"
            "agents/qa-test/invoke/sync"
        )
        assert req.method == "POST"
        body = json.loads(req.data)
        assert body == {"query": "Why?"}

    def test_returns_parsed_result(self):
        with mock_urlopen_json(INVOKE_RESULT):
            got = make_resource().invoke_sync(ORG, PROJECT, AGENT, query="q")
        assert isinstance(got, AgentInvokeResult)
        assert got.runId == "run-1"
        assert got.response == "Polio cases dropped [1]."
        assert got.status == "succeeded"
        assert len(got.sources) == 1
        assert got.sources[0].filename == "paper.pdf"
        assert got.sources[0].collectionName == "Polio"

    def test_warnings_are_optional(self):
        with mock_urlopen_json(INVOKE_RESULT):
            got = make_resource().invoke_sync(ORG, PROJECT, AGENT, query="q")
        assert got.warnings is None

    def test_warnings_carried_through_when_present(self):
        with mock_urlopen_json({**INVOKE_RESULT, "warnings": ["timeout"]}):
            got = make_resource().invoke_sync(ORG, PROJECT, AGENT, query="q")
        assert got.warnings == ["timeout"]


class TestStream:
    def test_yields_typed_events_in_order(self):
        events = [
            {"type": "run_started", "runId": "run-1"},
            {"type": "chunk", "content": "Polio "},
            {"type": "chunk", "content": "cases."},
            {
                "type": "done",
                "runId": "run-1",
                "status": "succeeded",
                "response": "Polio cases.",
                "iterationsUsed": 2,
                "sources": [SOURCE],
            },
        ]
        with mock_sse_urlopen(events):
            got = list(make_resource().stream(ORG, PROJECT, AGENT, query="why"))

        assert isinstance(got[0], AgentRunEventStarted)
        assert got[0].runId == "run-1"
        assert isinstance(got[1], AgentRunEventChunk)
        assert got[1].content == "Polio "
        assert isinstance(got[3], AgentRunEventDone)
        assert got[3].response == "Polio cases."
        assert len(got[3].sources) == 1
        assert got[3].sources[0].sectionTitle == "Methods"

    def test_posts_query_to_invoke_url(self):
        with mock_sse_urlopen([]) as mock_open:
            list(make_resource().stream(ORG, PROJECT, AGENT, query="why?"))
            req = mock_open.call_args[0][0]
        assert req.full_url == (
            "https://api.example.com/orgs/org-uuid-1/projects/proj-uuid-2/"
            "agents/qa-test/invoke"
        )
        assert req.method == "POST"
        assert json.loads(req.data) == {"query": "why?"}
