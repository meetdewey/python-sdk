"""Documents resource."""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, List, Optional, Union

from ..client import DeweyHttpClient
from ..types import Document, UploadUrlResponse

FileInput = Union[Path, IO[bytes], bytes]


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
