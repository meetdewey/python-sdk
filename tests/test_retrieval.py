"""Tests for RetrievalResource."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from dewey.client import DeweyHttpClient
from dewey.resources.retrieval import RetrievalResource

RETRIEVAL_RESULT = {
    "score": 0.9,
    "chunk": {"id": "c1", "content": "text", "position": 0, "tokenCount": 10},
    "section": {"id": "s1", "title": "Intro", "level": 1},
    "document": {"id": "d1", "filename": "doc.pdf"},
}


def make_resource() -> RetrievalResource:
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return RetrievalResource(client)


def mock_urlopen(body, status=200):
    raw = json.dumps(body).encode()
    resp = MagicMock()
    resp.status = status
    resp.headers.get = lambda k, d="": "application/json" if k == "Content-Type" else d
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=resp)


class TestRetrievalQuery:
    def test_sends_query(self):
        with mock_urlopen([RETRIEVAL_RESULT]) as mock_open:
            make_resource().query("col-1", "what is X?")
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["q"] == "what is X?"

    def test_sends_tags_filter(self):
        with mock_urlopen([]) as mock_open:
            make_resource().query("col-1", "q", tags=["annual", "finance"])
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["tags"] == ["annual", "finance"]

    def test_maps_any_tags_to_camel_case(self):
        with mock_urlopen([]) as mock_open:
            make_resource().query("col-1", "q", any_tags=["a", "b"])
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["anyTags"] == ["a", "b"]
        assert "any_tags" not in body

    def test_sends_metadata_filter(self):
        with mock_urlopen([]) as mock_open:
            make_resource().query("col-1", "q", metadata={"region": "us"})
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["metadata"] == {"region": "us"}

    def test_omits_filter_fields_when_not_set(self):
        with mock_urlopen([]) as mock_open:
            make_resource().query("col-1", "q")
            body = json.loads(mock_open.call_args[0][0].data)
        assert "tags" not in body
        assert "anyTags" not in body
        assert "metadata" not in body

    def test_sends_limit(self):
        with mock_urlopen([]) as mock_open:
            make_resource().query("col-1", "q", limit=5)
            body = json.loads(mock_open.call_args[0][0].data)
        assert body["limit"] == 5
