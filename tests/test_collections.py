"""Tests for CollectionsResource."""

import json
from unittest.mock import MagicMock, patch

from dewey.client import DeweyHttpClient
from dewey.resources.collections import CollectionsResource


def make_resource():
    client = DeweyHttpClient(api_key="test-key", base_url="https://api.example.com")
    return CollectionsResource(client)


def mock_urlopen(body, status=200, content_type="application/json"):
    """Patch urllib.request.urlopen to return a fake response."""
    if isinstance(body, (dict, list)):
        raw = json.dumps(body).encode()
    elif isinstance(body, bytes):
        raw = body
    else:
        raw = body.encode()

    resp = MagicMock()
    resp.status = status
    resp.headers.get = lambda key, default="": content_type if key == "Content-Type" else default
    resp.read.return_value = raw
    # MagicMock sets magic methods on the type; lambda s: s acts as `lambda self: self`
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=resp)


COLLECTION = {
    "id": "col-1",
    "name": "Docs",
    "visibility": "private",
    "projectId": "proj-1",
    "embeddingModel": "text-embedding-3-small",
    "chunkSize": 512,
    "chunkOverlap": 64,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
}


class TestCollectionsResource:
    def test_list_calls_get_collections(self):
        with mock_urlopen([]) as mock_open:
            make_resource().list()
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections"
            assert req.get_method() == "GET"

    def test_get_calls_get_collections_id(self):
        with mock_urlopen(COLLECTION) as mock_open:
            make_resource().get("col-1")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections/col-1"
            assert req.get_method() == "GET"

    def test_create_posts_with_body(self):
        with mock_urlopen(COLLECTION, status=201) as mock_open:
            make_resource().create("Docs")
            req = mock_open.call_args[0][0]
            assert req.get_method() == "POST"
            assert json.loads(req.data) == {"name": "Docs"}

    def test_update_patches_with_body(self):
        with mock_urlopen(COLLECTION) as mock_open:
            make_resource().update("col-1", name="Updated")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections/col-1"
            assert req.get_method() == "PATCH"
            assert json.loads(req.data)["name"] == "Updated"

    def test_delete_calls_delete_collections_id(self):
        with mock_urlopen(b"", status=204) as mock_open:
            result = make_resource().delete("col-1")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://api.example.com/collections/col-1"
            assert req.get_method() == "DELETE"
            assert result is None
