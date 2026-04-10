"""Tests for DocumentsResource.upload_many."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from dewey.client import DeweyHttpClient
from dewey.resources.documents import DocumentsResource, UploadManyItem
from dewey.types import Document

BASE_DOC = {
    "id": "doc-1",
    "collectionId": "col-1",
    "filename": "test.pdf",
    "storageKey": "key-1",
    "markdownStorageKey": None,
    "status": "processing",
    "fileSizeBytes": 1024,
    "markdownFileSizeBytes": None,
    "sectionCount": None,
    "chunkCount": None,
    "contentHash": None,
    "errorMessage": None,
    "createdAt": "2024-01-01T00:00:00Z",
}


def make_resource() -> DocumentsResource:
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return DocumentsResource(client)


def mock_urlopen_seq(responses: list[dict]):
    """Return a mock urlopen that cycles through a sequence of responses."""
    calls = iter(responses)

    def _open(req):
        cfg = next(calls)
        raw = json.dumps(cfg.get("body", {})).encode()
        resp = MagicMock()
        resp.status = cfg.get("status", 200)
        resp.headers.get = lambda k, d="": "application/json" if k == "Content-Type" else d
        resp.read.return_value = raw
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    return patch("urllib.request.urlopen", side_effect=_open)


class TestUploadMany:
    def test_upload_url_then_put_then_confirm(self):
        """Happy path: requestUploadUrl → S3 PUT → confirm."""
        resource = make_resource()

        url_resp = {"documentId": "doc-1", "uploadUrl": "https://s3.example.com/x"}
        confirm_resp = BASE_DOC

        with mock_urlopen_seq([
            {"body": url_resp},     # requestUploadUrl (POST to API)
            {"body": {}, "status": 200},  # S3 PUT (PUT to s3.example.com)
            {"body": confirm_resp}, # confirm (POST to API)
        ]):
            docs = resource.upload_many("col-1", [Path(__file__).parent / "__init__.py"])

        assert len(docs) == 1
        assert docs[0].id == "doc-1"

    def test_dedup_skips_put_and_confirm(self):
        """When uploadUrl is None the API returns the existing doc directly."""
        resource = make_resource()

        url_resp = {"documentId": "doc-1", "uploadUrl": None, "document": BASE_DOC}

        with mock_urlopen_seq([{"body": url_resp}]) as mock_open:
            docs = resource.upload_many("col-1", [b"duplicate content"])

        assert docs[0].id == "doc-1"
        assert mock_open.call_count == 1  # only the upload-url call

    def test_accepts_path_bytes_and_upload_many_item(self, tmp_path):
        """All three input types normalise correctly."""
        resource = make_resource()
        pdf = tmp_path / "a.pdf"
        pdf.write_bytes(b"pdf data")

        url_resp = {"documentId": "doc-1", "uploadUrl": None, "document": BASE_DOC}

        inputs = [
            pdf,                                          # Path
            b"raw bytes",                                 # bytes
            UploadManyItem(file=BytesIO(b"io"), filename="b.pdf"),  # UploadManyItem
        ]

        with mock_urlopen_seq([
            {"body": url_resp},
            {"body": url_resp},
            {"body": url_resp},
        ]) as mock_open:
            docs = resource.upload_many("col-1", inputs)

        assert len(docs) == 3
        assert mock_open.call_count == 3

    def test_on_progress_called_after_each_file(self):
        resource = make_resource()

        url_resp = {"documentId": "doc-1", "uploadUrl": None, "document": BASE_DOC}

        progress = []

        with mock_urlopen_seq([{"body": url_resp}, {"body": url_resp}]):
            resource.upload_many(
                "col-1",
                [b"file-a", b"file-b"],
                on_progress=lambda doc, completed, total: progress.append((doc.id, completed, total)),
            )

        assert len(progress) == 2
        totals = {t for _, _, t in progress}
        assert totals == {2}
        completeds = {c for _, c, _ in progress}
        assert completeds == {1, 2}

    def test_result_order_matches_input_order(self):
        """Results must be in the same order as the input list."""
        resource = make_resource()

        doc_a = {**BASE_DOC, "id": "doc-a"}
        doc_b = {**BASE_DOC, "id": "doc-b"}

        with mock_urlopen_seq([
            {"body": {"documentId": "doc-a", "uploadUrl": None, "document": doc_a}},
            {"body": {"documentId": "doc-b", "uploadUrl": None, "document": doc_b}},
        ]):
            docs = resource.upload_many("col-1", [b"aaa", b"bbb"])

        assert docs[0].id == "doc-a"
        assert docs[1].id == "doc-b"

    def test_s3_error_propagates(self):
        """An S3 PUT failure should raise RuntimeError."""
        resource = make_resource()

        url_resp = {"documentId": "doc-1", "uploadUrl": "https://s3.example.com/x"}

        # S3 PUT returns 403
        s3_resp = MagicMock()
        s3_resp.status = 403
        s3_resp.__enter__ = lambda s: s
        s3_resp.__exit__ = MagicMock(return_value=False)

        def _open(req):
            if "s3.example.com" in req.full_url:
                return s3_resp
            raw = json.dumps(url_resp).encode()
            resp = MagicMock()
            resp.status = 200
            resp.headers.get = lambda k, d="": "application/json" if k == "Content-Type" else d
            resp.read.return_value = raw
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=_open):
            with pytest.raises(RuntimeError, match="S3 upload failed"):
                resource.upload_many("col-1", [b"data"])
