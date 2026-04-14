"""Core HTTP client for the Dewey API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Generator, Optional, Tuple


class DeweyError(Exception):
    """Raised when the Dewey API returns a non-2xx response."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message

    def __repr__(self) -> str:
        return f"DeweyError(status={self.status!r}, message={self.message!r})"


def _build_multipart(
    fields: Dict[str, str],
    file_field: str,
    filename: str,
    file_data: bytes,
    content_type: str,
) -> Tuple[bytes, str]:
    """Build a multipart/form-data body. Returns (body_bytes, content_type_header)."""
    boundary = "----DeweyBoundary7MA4YWxkTrZu0gW"
    lines: list[bytes] = []

    for name, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        lines.append(b"")
        lines.append(value.encode())

    lines.append(f"--{boundary}".encode())
    lines.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode()
    )
    lines.append(f"Content-Type: {content_type}".encode())
    lines.append(b"")
    lines.append(file_data)
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")

    body = b"\r\n".join(lines)
    header = f"multipart/form-data; boundary={boundary}"
    return body, header


class DeweyHttpClient:
    """Shared low-level HTTP client used by all resource classes."""

    def __init__(self, api_key: str, base_url: str = "https://api.meetdewey.com/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Any] = None,
        multipart: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP request. Returns the parsed JSON body (or plain str for
        text responses, or None for 204).
        """
        url = self._url(path)
        headers = self._auth_headers()
        data: Optional[bytes] = None

        if multipart is not None:
            fields = {k: v for k, v in multipart.items() if isinstance(v, str)}
            file_info = multipart.get("__file__")
            if file_info:
                raw_body, ct_header = _build_multipart(
                    fields=fields,
                    file_field=file_info["field"],
                    filename=file_info["filename"],
                    file_data=file_info["data"],
                    content_type=file_info["content_type"],
                )
                data = raw_body
                headers["Content-Type"] = ct_header
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                if status == 204:
                    return None
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()
                if "text/" in content_type:
                    return raw.decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            status = exc.code
            message = exc.reason
            try:
                raw = exc.read()
                err_body = json.loads(raw)
                message = err_body.get("message") or err_body.get("error") or message
            except Exception:
                pass
            raise DeweyError(status, message) from exc

    def stream_sse_get(
        self,
        path: str,
    ) -> Generator[dict, None, None]:
        """
        GET an SSE endpoint and yield parsed JSON event payloads.
        Parses ``data: {...}\\n\\n`` lines using urllib (no third-party deps).
        """
        url = self._url(path)
        headers = {
            **self._auth_headers(),
            "Accept": "text/event-stream",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            status = exc.code
            message = exc.reason
            try:
                raw = exc.read()
                err_body = json.loads(raw)
                message = err_body.get("message") or err_body.get("error") or message
            except Exception:
                pass
            raise DeweyError(status, message) from exc

        try:
            buf = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n\n" in buf:
                    message_bytes, buf = buf.split(b"\n\n", 1)
                    for line in message_bytes.split(b"\n"):
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            payload = line_str[6:].strip()
                            if payload == "[DONE]":
                                return
                            try:
                                yield json.loads(payload)
                            except json.JSONDecodeError:
                                pass

            if buf.strip():
                for line in buf.split(b"\n"):
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        payload = line_str[6:].strip()
                        if payload and payload != "[DONE]":
                            try:
                                yield json.loads(payload)
                            except json.JSONDecodeError:
                                pass
        finally:
            resp.close()

    def stream_sse(
        self,
        path: str,
        body: Any,
    ) -> Generator[dict, None, None]:
        """
        POST to an SSE endpoint and yield parsed JSON event payloads.
        Parses ``data: {...}\\n\\n`` lines using urllib (no third-party deps).
        """
        url = self._url(path)
        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            status = exc.code
            message = exc.reason
            try:
                raw = exc.read()
                err_body = json.loads(raw)
                message = err_body.get("message") or err_body.get("error") or message
            except Exception:
                pass
            raise DeweyError(status, message) from exc

        try:
            buf = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buf += chunk
                # SSE messages are separated by \n\n
                while b"\n\n" in buf:
                    message_bytes, buf = buf.split(b"\n\n", 1)
                    for line in message_bytes.split(b"\n"):
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            payload = line_str[6:].strip()
                            if payload == "[DONE]":
                                return
                            try:
                                yield json.loads(payload)
                            except json.JSONDecodeError:
                                pass

            # Flush remaining buffer
            if buf.strip():
                for line in buf.split(b"\n"):
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        payload = line_str[6:].strip()
                        if payload and payload != "[DONE]":
                            try:
                                yield json.loads(payload)
                            except json.JSONDecodeError:
                                pass
        finally:
            resp.close()
