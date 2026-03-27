"""Provider Keys resource."""

from __future__ import annotations

from typing import List, Literal

from ..client import DeweyHttpClient
from ..types import ProviderKey

ProviderName = Literal["openai", "cohere", "voyageai"]


class ProviderKeysResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def create(
        self,
        project_id: str,
        provider: ProviderName,
        key: str,
        name: str,
    ) -> ProviderKey:
        """Add a provider API key to a project."""
        body = {"provider": provider, "key": key, "name": name}
        data = self._client.request(
            "POST", f"/projects/{project_id}/provider-keys", body=body
        )
        return ProviderKey.from_dict(data)

    def list(self, project_id: str) -> List[ProviderKey]:
        """List all provider keys for a project."""
        data = self._client.request("GET", f"/projects/{project_id}/provider-keys")
        return [ProviderKey.from_dict(k) for k in data]

    def delete(self, project_id: str, key_id: str) -> None:
        """Delete a provider key. Returns None on success."""
        self._client.request(
            "DELETE", f"/projects/{project_id}/provider-keys/{key_id}"
        )
