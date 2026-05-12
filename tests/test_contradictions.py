"""Tests for ContradictionsResource."""

import json
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from dewey.client import DeweyHttpClient
from dewey.resources.contradictions import ContradictionsResource


def make_resource():
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return ContradictionsResource(client)


def mock_urlopen(body, status=200, content_type="application/json"):
    if isinstance(body, (dict, list)):
        raw = json.dumps(body).encode()
    elif isinstance(body, bytes):
        raw = body
    else:
        raw = body.encode()

    resp = MagicMock()
    resp.status = status
    resp.headers.get = lambda key, default="": (
        content_type if key == "Content-Type" else default
    )
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=resp)


def parsed_query(req):
    return parse_qs(urlparse(req.full_url).query)


class TestContradictionsList:
    def test_list_calls_get_with_no_query_by_default(self):
        with mock_urlopen({"total": 0, "items": []}) as mock_open:
            make_resource().list("col-1")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections/col-1/contradictions"
            assert req.get_method() == "GET"

    def test_list_forwards_severity_status_limit(self):
        with mock_urlopen({"total": 0, "items": []}) as mock_open:
            make_resource().list(
                "col-1", severity="high", status="dismissed", limit=50
            )
            qs = parsed_query(mock_open.call_args[0][0])
            assert qs["severity"] == ["high"]
            assert qs["status"] == ["dismissed"]
            assert qs["limit"] == ["50"]

    def test_list_forwards_document_id(self):
        with mock_urlopen({"total": 0, "items": []}) as mock_open:
            make_resource().list("col-1", document_id="doc-42")
            qs = parsed_query(mock_open.call_args[0][0])
            assert qs["documentId"] == ["doc-42"]


class TestContradictionsListFiles:
    def test_list_files_calls_get_files_endpoint(self):
        with mock_urlopen({"files": []}) as mock_open:
            make_resource().list_files("col-1")
            req = mock_open.call_args[0][0]
            assert (
                req.full_url
                == "https://api.example.com/collections/col-1/contradictions/files"
            )
            assert req.get_method() == "GET"

    def test_list_files_forwards_status_and_severity(self):
        with mock_urlopen({"files": []}) as mock_open:
            make_resource().list_files("col-1", status="applied", severity="medium")
            qs = parsed_query(mock_open.call_args[0][0])
            assert qs["status"] == ["applied"]
            assert qs["severity"] == ["medium"]

    def test_list_files_returns_parsed_file_list(self):
        payload = {
            "files": [
                {
                    "documentId": "doc-a",
                    "filename": "submission.pdf",
                    "contradictionCount": 5,
                },
                {
                    "documentId": "doc-b",
                    "filename": "review.pdf",
                    "contradictionCount": 2,
                },
            ]
        }
        with mock_urlopen(payload):
            result = make_resource().list_files("col-1")
            assert len(result.files) == 2
            assert result.files[0].documentId == "doc-a"
            assert result.files[0].filename == "submission.pdf"
            assert result.files[0].contradictionCount == 5


class TestContradictionsDetect:
    def test_detect_posts(self):
        payload = {"runId": "r1", "status": "pending", "enqueuedAt": "2025-01-01T00:00:00Z"}
        with mock_urlopen(payload) as mock_open:
            make_resource().detect("col-1")
            req = mock_open.call_args[0][0]
            assert (
                req.full_url
                == "https://api.example.com/collections/col-1/contradictions/detect"
            )
            assert req.get_method() == "POST"


class TestContradictionsDismiss:
    def test_dismiss_patches_with_status_dismissed(self):
        payload = {
            "id": "c1",
            "severity": "high",
            "status": "dismissed",
            "explanation": "...",
            "suggestedInstruction": None,
            "clusterTopicSummary": None,
            "createdAt": "2025-01-01T00:00:00Z",
            "claims": [],
        }
        with mock_urlopen(payload) as mock_open:
            make_resource().dismiss("col-1", "c1")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections/col-1/contradictions/c1"
            assert req.get_method() == "PATCH"
            assert json.loads(req.data) == {"status": "dismissed"}


class TestContradictionsApplyInstruction:
    def test_apply_instruction_posts_empty_body_when_none(self):
        with mock_urlopen({}) as mock_open:
            make_resource().apply_instruction("col-1", "c1")
            req = mock_open.call_args[0][0]
            assert (
                req.full_url
                == "https://api.example.com/collections/col-1/contradictions/c1/apply-instruction"
            )
            assert json.loads(req.data) == {}

    def test_apply_instruction_posts_override(self):
        with mock_urlopen({}) as mock_open:
            make_resource().apply_instruction("col-1", "c1", "Use the 2024 report.")
            req = mock_open.call_args[0][0]
            assert json.loads(req.data) == {"instruction": "Use the 2024 report."}
