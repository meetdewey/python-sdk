"""Documents resource."""

from __future__ import annotations

import hashlib
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Callable, List, Optional, Union

from ..client import DeweyHttpClient
from ..types import Document, UploadUrlResponse

FileInput = Union[Path, IO[bytes], bytes]


@dataclass
class UploadManyItem:
    """Wraps a file with optional metadata for :meth:`DocumentsResource.upload_many`."""

    file: FileInput
    filename: Optional[str] = None
    content_type: Optional[str] = None


def _read_file(
    file: FileInput,
    filename: Optional[str],
    content_type: Optional[str],
) -> tuple[bytes, str, str]:
    """Read a file-like input and return (data, filename, content_type)."""
    if isinstance(file, Path):
        data = file.read_bytes()
        fname = filename or file.name
        ct = content_type or "application/octet-stream"
        return data, fname, ct

    if isinstance(file, bytes):
        fname = filename or "upload"
        ct = content_type or "application/octet-stream"
        return file, fname, ct

    # File-like object
    data = file.read()
    if isinstance(data, str):
        data = data.encode("utf-8")
    fname = filename or getattr(file, "name", "upload")
    # Strip directory component if it's a real path
    fname = os.path.basename(fname)
    ct = content_type or "application/octet-stream"
    return data, fname, ct


class DocumentsResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def upload(
        self,
        collection_id: str,
        file: FileInput,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        content_hash: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Document:
        """
        Upload a document via multipart/form-data.

        ``file`` can be a ``pathlib.Path``, a bytes object, or any binary
        file-like object (e.g. an ``open()`` handle or ``io.BytesIO``).
        """
        data, fname, ct = _read_file(file, filename, content_type)

        extra_fields: dict = {}
        if name:
            extra_fields["name"] = name
        if content_hash:
            extra_fields["contentHash"] = content_hash

        multipart = {
            **extra_fields,
            "__file__": {
                "field": "file",
                "filename": fname,
                "data": data,
                "content_type": ct,
            },
        }
        result = self._client.request(
            "POST",
            f"/collections/{collection_id}/documents",
            multipart=multipart,
        )
        return Document.from_dict(result)

    def request_upload_url(
        self,
        collection_id: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        content_hash: str,
    ) -> UploadUrlResponse:
        """Request a presigned S3 upload URL."""
        body = {
            "filename": filename,
            "contentType": content_type,
            "fileSizeBytes": file_size_bytes,
            "contentHash": content_hash,
        }
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/documents/upload-url",
            body=body,
        )
        return UploadUrlResponse.from_dict(data)

    def confirm(self, collection_id: str, document_id: str) -> Document:
        """Confirm a presigned upload and trigger ingestion."""
        data = self._client.request(
            "POST",
            f"/collections/{collection_id}/documents/{document_id}/confirm",
        )
        return Document.from_dict(data)

    def list(self, collection_id: str) -> List[Document]:
        """List all documents in a collection."""
        data = self._client.request("GET", f"/collections/{collection_id}/documents")
        return [Document.from_dict(d) for d in data]

    def get(self, collection_id: str, document_id: str) -> Document:
        """Get a document by ID."""
        data = self._client.request("GET", f"/documents/{document_id}")
        return Document.from_dict(data)

    def get_markdown(self, collection_id: str, document_id: str) -> str:
        """Fetch the rendered Markdown for a document. Returns a string."""
        return self._client.request("GET", f"/documents/{document_id}/markdown")

    def retry(self, collection_id: str, document_id: str) -> Document:
        """Retry a document that is in an error state."""
        data = self._client.request("POST", f"/documents/{document_id}/retry")
        return Document.from_dict(data)

    def delete(self, collection_id: str, document_id: str) -> None:
        """Delete a document. Returns None on success."""
        self._client.request("DELETE", f"/documents/{document_id}")

    def upload_many(
        self,
        collection_id: str,
        files: List[Union[FileInput, UploadManyItem]],
        *,
        concurrency: int = 5,
        on_progress: Optional[Callable[[Document, int, int], None]] = None,
    ) -> List[Document]:
        """Upload multiple files efficiently using presigned S3 URLs.

        Each file is uploaded directly to S3 (bypassing the API server), so
        there are no payload-size limits and throughput scales with your
        network.  Files are uploaded ``concurrency`` at a time (default 5).

        If a file's SHA-256 hash matches an existing document, the API returns
        the existing document immediately — no upload or confirm round-trip.

        ``files`` can be a flat list of :class:`pathlib.Path` objects, bytes,
        file-like objects, or :class:`UploadManyItem` instances when you need
        to supply a custom filename or content-type.

        Example::

            from pathlib import Path
            docs = client.documents.upload_many(
                collection_id,
                list(Path("./reports").glob("**/*.pdf")),
                concurrency=10,
                on_progress=lambda doc, n, total: print(f"{n}/{total} {doc.filename}"),
            )
        """
        total = len(files)
        results: List[Optional[Document]] = [None] * total

        def _upload_one(item: Union[FileInput, UploadManyItem], index: int) -> Document:
            # Normalise to UploadManyItem
            if not isinstance(item, UploadManyItem):
                item = UploadManyItem(file=item)

            data, filename, content_type = _read_file(
                item.file, item.filename, item.content_type
            )
            content_hash = hashlib.sha256(data).hexdigest()

            url_resp = self.request_upload_url(
                collection_id,
                filename=filename,
                content_type=content_type,
                file_size_bytes=len(data),
                content_hash=content_hash,
            )

            if url_resp.uploadUrl is None:
                # Dedup hit — file already exists
                doc = url_resp.document
                if doc is None:
                    raise RuntimeError(
                        f"API returned no uploadUrl and no document for '{filename}'"
                    )
            else:
                # PUT directly to S3 — auth is baked into the presigned URL
                s3_req = urllib.request.Request(
                    url_resp.uploadUrl, data=data, method="PUT"
                )
                s3_req.add_header("Content-Type", content_type)
                with urllib.request.urlopen(s3_req) as s3_resp:
                    if s3_resp.status not in (200, 204):
                        raise RuntimeError(
                            f"S3 upload failed with status {s3_resp.status}"
                        )
                doc = self.confirm(collection_id, url_resp.documentId)

            return doc

        completed = 0

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_index = {
                executor.submit(_upload_one, item, i): i
                for i, item in enumerate(files)
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                doc = future.result()  # re-raises any exception
                results[index] = doc
                completed += 1
                if on_progress is not None:
                    on_progress(doc, completed, total)

        return results  # type: ignore[return-value]
