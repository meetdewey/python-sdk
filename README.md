<p align="center">
  <a href="https://meetdewey.com">
    <img src="./logo.png" alt="Dewey" width="120" />
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
| `stats(collection_id)` | Document count, storage, section/chunk/claim counts |
| `recompute_summaries(collection_id)` | Re-run AI section summarization |
| `recompute_captions(collection_id)` | Re-run AI captioning for images and tables |
| `recompute_claims(collection_id)` | Re-extract factual claims (clears existing) |

`update()` accepts: `name`, `visibility`, `chunk_size`, `chunk_overlap`, `description`, `enable_summarization`, `enable_captioning`, `llm_model`, `instructions`. `llm_model` and `instructions` accept `None` to clear the field; omit them entirely to leave unchanged.

```python
# Set research instructions for a collection
client.collections.update(
    collection_id,
    instructions="All figures are in USD unless stated otherwise.",
)

# Clear instructions
client.collections.update(collection_id, instructions=None)

# Get collection statistics
stats = client.collections.stats(collection_id)
print(f"{stats.docCount} docs, {stats.totalClaimsCount} claims")
```

### `client.documents`

| Method | Description |
|---|---|
| `upload(collection_id, file, *, filename, content_type, ...)` | Multipart upload |
| `upload_many(collection_id, files, *, concurrency, on_progress)` | Bulk upload via presigned S3 URLs |
| `request_upload_url(collection_id, filename, content_type, file_size_bytes, content_hash)` | Presigned URL |
| `confirm(collection_id, document_id)` | Confirm presigned upload |
| `list(collection_id)` | List documents |
| `get(collection_id, document_id)` | Get document |
| `get_markdown(collection_id, document_id)` | Get Markdown string |
| `retry(collection_id, document_id)` | Retry failed document |
| `delete(collection_id, document_id)` | Delete document |

`upload()` accepts a `pathlib.Path`, `bytes`, or any binary file-like object.

`upload_many()` is the recommended approach for large datasets. Each file is uploaded directly to S3 (bypassing the API server), so there are no payload-size limits. Files that match an existing document's hash are deduplicated automatically.

```python
from pathlib import Path

docs = client.documents.upload_many(
    collection_id,
    list(Path("./reports").glob("**/*.pdf")),
    concurrency=10,
    on_progress=lambda doc, n, total: print(f"{n}/{total} {doc.filename}"),
)
```

Pass `UploadManyItem` instances when you need a custom filename or content type:

```python
from dewey.resources.documents import UploadManyItem
from io import BytesIO

items = [
    UploadManyItem(file=BytesIO(data), filename="custom-name.pdf", content_type="application/pdf"),
]
docs = client.documents.upload_many(collection_id, items)
```

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

### `client.claims`

| Method | Description |
|---|---|
| `map_stream(collection_id)` | SSE stream of all claims with UMAP coordinates |
| `list_by_document(document_id, *, min_importance)` | Claims extracted from a specific document |

`map_stream()` yields raw event dicts. Check `event["type"]`: `"progress"`, `"done"` (with `claims` list), or `"error"`.

```python
from dewey.types import ClaimMapItem

for event in client.claims.map_stream(collection_id):
    if event["type"] == "done":
        claims = [ClaimMapItem.from_dict(c) for c in event["claims"]]
        for claim in claims:
            print(f"[{claim.importance}] {claim.text}")

# Per-document claims (fast, no SSE)
result = client.claims.list_by_document(document_id, min_importance=3)
for claim in result.claims:
    print(claim.text)
```

### `client.contradictions`

| Method | Description |
|---|---|
| `list(collection_id, *, severity, status, limit)` | List detected contradictions |
| `detect(collection_id)` | Trigger async contradiction detection run |
| `get_latest_run(collection_id)` | Poll status of the latest detection run |
| `dismiss(collection_id, contradiction_id)` | Mark a contradiction as ignored |
| `apply_instruction(collection_id, contradiction_id, instruction)` | Apply resolution; appends to collection instructions |

```python
# Trigger detection
run = client.contradictions.detect(collection_id)
print("Run ID:", run.runId)

# Later: poll status
status = client.contradictions.get_latest_run(collection_id)
print(status.status, status.contradictionsFound)

# List active contradictions and apply resolutions
result = client.contradictions.list(collection_id, status="active")
for c in result.items:
    print(c.severity, c.explanation)
    # Apply the suggested resolution
    client.contradictions.apply_instruction(collection_id, c.id)
```

### `client.duplicates`

Fuzzy document deduplication. Identifies near-duplicate documents via MinHash signatures, marks one member of each cluster as canonical, and excludes near-duplicates from retrieval and contradiction detection. Must be enabled per-collection with `client.collections.update(id, enable_deduplication=True)`.

| Method | Description |
|---|---|
| `detect(collection_id)` | Trigger async dedup run across all ready documents |
| `get_latest_run(collection_id)` | Poll status of the latest dedup run |
| `list(collection_id, *, limit, offset)` | List duplicate groups with members and coverage percentages |
| `promote_canonical(collection_id, group_id, canonical_document_id)` | Promote a different member to canonical; old canonical becomes near_duplicate |
| `disband(collection_id, group_id)` | Disband a group; all former members rejoin retrieval as distinct |

```python
# Enable on a collection (one-time)
client.collections.update(collection_id, enable_deduplication=True)

# Trigger detection, then poll
run = client.duplicates.detect(collection_id)
status = client.duplicates.get_latest_run(collection_id)
print(status.status, status.duplicateGroupsCreated)

# Review groups
result = client.duplicates.list(collection_id)
for group in result.items:
    for m in group.members:
        if m.relationship == "near_duplicate":
            pct = round((m.coverageToCanonical or 0) * 100)
            print(f"{m.filename} covers {pct}% of canonical")
```

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

For single files or when you need manual control, use the low-level presigned URL flow. For bulk ingestion, prefer `upload_many()` which handles this automatically with concurrency.

```python
import hashlib
import urllib.request
from pathlib import Path

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

# 2. PUT bytes directly to S3 (no auth header needed)
req = urllib.request.Request(resp.uploadUrl, data=data, method="PUT")
req.add_header("Content-Type", "application/pdf")
urllib.request.urlopen(req)

# 3. Confirm to trigger ingestion
doc = client.documents.confirm(collection_id, resp.documentId)
```
