"""Tests for DeweyHttpClient."""

import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from dewey.client import DeweyError, DeweyHttpClient


def make_client():
    return DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")


def mock_response(body, status=200, content_type="application/json"):
    """Build a mock urllib response."""
    if isinstance(body, (dict, list)):
        raw = json.dumps(body).encode()
    elif isinstance(body, str):
        raw = body.encode()
    else:
        raw = body

    resp = MagicMock()
    resp.status = status
    resp.headers = MagicMock()
    resp.headers.get = lambda key, default="": (
        content_type if key == "Content-Type" else default
    )
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def mock_http_error(status, body=None, reason="Error"):
    """Build a urllib HTTPError."""
    raw = json.dumps(body).encode() if body else b""
    err = urllib.error.HTTPError(
        url="http://x",
        code=status,
        msg=reason,
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(raw),
    )
    return err


# ── request ───────────────────────────────────────────────────────────────────


class TestRequest:
    def test_builds_correct_url(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: mock_response({})
            mock_open.return_value = mock_response({})
            client.request("GET", "/collections")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections"

    def test_sets_authorization_header(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = mock_response({})
            client.request("GET", "/collections")
            req = mock_open.call_args[0][0]
            assert req.get_header("Authorization") == "Bearer test-key"

    def test_returns_parsed_json(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = mock_response([{"id": "col-1"}])
            result = client.request("GET", "/collections")
            assert result == [{"id": "col-1"}]

    def test_returns_none_on_204(self):
        client = make_client()
        resp = mock_response(b"", status=204)
        with patch("urllib.request.urlopen", return_value=resp):
            result = client.request("DELETE", "/collections/col-1")
            assert result is None

    def test_returns_text_for_text_content_type(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = mock_response("hello world", content_type="text/plain")
            result = client.request("GET", "/text")
            assert result == "hello world"

    def test_sends_json_body(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = mock_response({"id": "col-1"}, status=201)
            client.request("POST", "/collections", body={"name": "Test"})
            req = mock_open.call_args[0][0]
            assert req.get_header("Content-type") == "application/json"
            assert json.loads(req.data) == {"name": "Test"}

    def test_raises_dewey_error_on_4xx(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = mock_http_error(404, {"error": "Not found"})
            with pytest.raises(DeweyError) as exc_info:
                client.request("GET", "/collections/bad")
            assert exc_info.value.status == 404
            assert exc_info.value.message == "Not found"

    def test_raises_dewey_error_uses_reason_when_no_json(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = mock_http_error(502, reason="Bad Gateway")
            with pytest.raises(DeweyError) as exc_info:
                client.request("GET", "/collections")
            assert exc_info.value.status == 502

    def test_strips_trailing_slash_from_base_url(self):
        client = DeweyHttpClient(api_key="k", base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com"


# ── stream_sse ────────────────────────────────────────────────────────────────


def make_sse_response(events):
    """Build a mock response that streams SSE events."""
    lines = []
    for event in events:
        lines.append(f"data: {json.dumps(event)}")
        lines.append("")
    body = "\n".join(lines).encode()

    resp = MagicMock()
    # Return chunks then empty bytes to end the loop
    chunks = [body[i : i + 4096] for i in range(0, len(body), 4096)] + [b""]
    resp.read.side_effect = chunks
    resp.close = MagicMock()
    return resp


class TestStreamSse:
    def test_yields_parsed_events(self):
        client = make_client()
        resp = make_sse_response([
            {"type": "chunk", "content": "Hello"},
            {"type": "chunk", "content": " world"},
        ])
        with patch("urllib.request.urlopen", return_value=resp):
            events = list(client.stream_sse("/research", {"q": "test"}))
        assert events == [
            {"type": "chunk", "content": "Hello"},
            {"type": "chunk", "content": " world"},
        ]

    def test_stops_on_done_sentinel(self):
        client = make_client()
        body = b"data: {\"type\":\"chunk\",\"content\":\"Hi\"}\n\ndata: [DONE]\n\ndata: {\"type\":\"ignored\"}\n\n"
        resp = MagicMock()
        resp.read.side_effect = [body, b""]
        resp.close = MagicMock()
        with patch("urllib.request.urlopen", return_value=resp):
            events = list(client.stream_sse("/research", {"q": "test"}))
        assert len(events) == 1
        assert events[0] == {"type": "chunk", "content": "Hi"}

    def test_skips_malformed_json_lines(self):
        client = make_client()
        body = b"data: not-json\n\ndata: {\"type\":\"done\"}\n\n"
        resp = MagicMock()
        resp.read.side_effect = [body, b""]
        resp.close = MagicMock()
        with patch("urllib.request.urlopen", return_value=resp):
            events = list(client.stream_sse("/research", {"q": "test"}))
        assert events == [{"type": "done"}]

    def test_raises_dewey_error_on_non_2xx(self):
        client = make_client()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = mock_http_error(401, {"error": "Unauthorized"})
            with pytest.raises(DeweyError) as exc_info:
                list(client.stream_sse("/research", {"q": "test"}))
            assert exc_info.value.status == 401
