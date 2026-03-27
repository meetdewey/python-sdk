<p align="center">
  <a href="https://meetdewey.com">
    <img src="https://meetdewey.com/logo.png" alt="Dewey" width="120" />
  </a>
</p>

# dewey

[![CI](https://github.com/meetdewey/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/meetdewey/python-sdk/actions/workflows/ci.yml)

Python client for the [Dewey](https://meetdewey.com) API. No third-party dependencies — uses only the Python standard library. See the [full API reference](https://meetdewey.com/docs) for details on all endpoints and types.

## Installation

```bash
pip install dewey
```

## Quick start

```python
from dewey import DeweyClient

client = DeweyClient(api_key="dwy_live_...")

# Create a collection
col = client.collections.create("My Docs")

# Upload a document
from pathlib import Path
doc = client.documents.upload(col.id, Path("report.pdf"))

# Query
results = client.retrieval.query(col.id, "What is the refund policy?")
for r in results:
    print(r.score, r.chunk.content[:100])

# Research (SSE streaming)
for event in client.research.stream(col.id, "Summarise key findings"):
    if event.type == "chunk":
        print(event.content, end="", flush=True)
    elif event.type == "done":
        print("\nSources:", event.sources)
```

## Constructor

```python
DeweyClient(api_key: str, base_url: str = "https://api.meetdewey.com/v1")
```

## Resources

### `client.collections`

| Method | Description |
|---|---|
| `create(name, *, visibility, chunk_size, chunk_overlap, embedding_model)` | Create a collection |
| `list()` | List collections |
| `get(collection_id)` | Get by ID |
| `update(collection_id, *, name, visibility, ...)` | Update |
| `delete(collection_id)` | Delete |

### `client.documents`

| Method | Description |
|---|---|
| `upload(collection_id, file, *, filename, content_type, ...)` | Multipart upload |
| `request_upload_url(collection_id, filename, content_type, file_size_bytes, content_hash)` | Presigned URL |
| `confirm(collection_id, document_id)` | Confirm presigned upload |
| `list(collection_id)` | List documents |
| `get(collection_id, document_id)` | Get document |
| `get_markdown(collection_id, document_id)` | Get Markdown string |
| `retry(collection_id, document_id)` | Retry failed document |
| `delete(collection_id, document_id)` | Delete document |

`upload()` accepts a `pathlib.Path`, `bytes`, or any binary file-like object.

### `client.sections`

| Method | Description |
|---|---|
| `list(collection_id, document_id)` | List sections |
| `get(section_id)` | Get section with content |
| `get_chunks(section_id)` | Get chunks |
| `scan(collection_id, query, *, top_k)` | Full-text section scan |

### `client.retrieval`

| Method | Description |
|---|---|
| `query(collection_id, q, *, limit)` | Hybrid search |

### `client.research`

| Method | Description |
|---|---|
| `stream(collection_id, q, *, depth, model)` | SSE research → `Generator[ResearchEvent]` |

`depth` options: `"quick"`, `"balanced"` (default), `"deep"`, `"exhaustive"`.

### `client.provider_keys`

| Method | Description |
|---|---|
| `create(project_id, provider, key, name)` | Add provider key |
| `list(project_id)` | List keys |
| `delete(project_id, key_id)` | Delete key |

## Error handling

```python
from dewey import DeweyClient, DeweyError

client = DeweyClient(api_key="dwy_live_...")

try:
    client.collections.get("unknown-id")
except DeweyError as e:
    print(e.status, e.message)  # e.g. 404 "Collection not found"
```

## Presigned upload flow

```python
import hashlib

data = Path("file.pdf").read_bytes()
content_hash = hashlib.sha256(data).hexdigest()

# 1. Request a presigned URL
resp = client.documents.request_upload_url(
    collection_id,
    filename="file.pdf",
    content_type="application/pdf",
    file_size_bytes=len(data),
    content_hash=content_hash,
)

# 2. PUT bytes directly to S3 (no auth header)
import urllib.request
req = urllib.request.Request(resp.uploadUrl, data=data, method="PUT")
req.add_header("Content-Type", "application/pdf")
urllib.request.urlopen(req)

# 3. Confirm to trigger ingestion
doc = client.documents.confirm(collection_id, resp.documentId)
```
