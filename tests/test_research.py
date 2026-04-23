"""Tests for ResearchResource."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from dewey.client import DeweyHttpClient
from dewey.resources.research import ResearchResource

RESEARCH_RESULT = {
    "answer": "X is Y.",
    "sessionId": "sess-1",
    "sources": [],
}


def make_resource() -> ResearchResource:
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return ResearchResource(client)


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


class TestResearchSync:
    def test_sends_query_and_depth(self):
        with mock_urlopen_json(RESEARCH_RESULT) as mock_open:
            make_resource().research_sync("col-1", "What is X?")
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["q"] == "What is X?"
        assert body["depth"] == "balanced"

    def test_sends_tags_filter(self):
        with mock_urlopen_json(RESEARCH_RESULT) as mock_open:
            make_resource().research_sync("col-1", "q", tags=["annual"])
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["tags"] == ["annual"]

    def test_maps_any_tags_to_camel_case(self):
        with mock_urlopen_json(RESEARCH_RESULT) as mock_open:
            make_resource().research_sync("col-1", "q", any_tags=["a", "b"])
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["anyTags"] == ["a", "b"]
        assert "any_tags" not in body

    def test_sends_metadata_filter(self):
        with mock_urlopen_json(RESEARCH_RESULT) as mock_open:
            make_resource().research_sync("col-1", "q", metadata={"region": "us"})
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["metadata"] == {"region": "us"}

    def test_omits_filter_fields_when_not_set(self):
        with mock_urlopen_json(RESEARCH_RESULT) as mock_open:
            make_resource().research_sync("col-1", "q")
            body = json.loads(mock_open.call_args[0][0].data)
        assert "tags" not in body
        assert "anyTags" not in body
        assert "metadata" not in body

    def test_returns_research_result(self):
        with mock_urlopen_json(RESEARCH_RESULT):
            result = make_resource().research_sync("col-1", "q")
        assert result.answer == "X is Y."
        assert result.sessionId == "sess-1"


class TestResearchStream:
    def test_sends_tags_any_tags_metadata_in_request(self):
        events = [{"type": "chunk", "content": "hi"}]
        with mock_sse_urlopen(events) as mock_open:
            list(make_resource().stream(
                "col-1",
                "q",
                tags=["t1"],
                any_tags=["a", "b"],
                metadata={"k": "v"},
            ))
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["tags"] == ["t1"]
        assert body["anyTags"] == ["a", "b"]
        assert "any_tags" not in body
        assert body["metadata"] == {"k": "v"}

    def test_omits_filter_fields_when_not_set(self):
        events = [{"type": "done", "sessionId": "s1", "sources": []}]
        with mock_sse_urlopen(events) as mock_open:
            list(make_resource().stream("col-1", "q"))
            body = json.loads(mock_open.call_args[0][0].data)
        assert "tags" not in body
        assert "anyTags" not in body
        assert "metadata" not in body

    def test_yields_events(self):
        events = [
            {"type": "chunk", "content": "Hello"},
            {"type": "done", "sessionId": "s1", "sources": []},
        ]
        with mock_sse_urlopen(events):
            result = list(make_resource().stream("col-1", "q"))
        assert result[0].type == "chunk"
        assert result[0].content == "Hello"
        assert result[1].type == "done"
