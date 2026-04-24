"""Provider Keys resource."""

from __future__ import annotations

from typing import List, Literal

from ..client import DeweyHttpClient
from ..types import ProviderKey

ProviderName = Literal["openai", "cohere", "voyageai"]


class ProviderKeysResource:
    def __init__(self, client: DeweyHttpClient) -> None:
        self._client = client

    def create(self, provider: ProviderName, key: str, name: str) -> ProviderKey:
        """Add a provider API key (org-scoped via API key auth)."""
        body = {"provider": provider, "key": key, "name": name}
        data = self._client.request("POST", "/provider-keys", body=body)
        return ProviderKey.from_dict(data)

    def list(self) -> List[ProviderKey]:
        """List all provider keys for the authenticated org."""
        data = self._client.request("GET", "/provider-keys")
        return [ProviderKey.from_dict(k) for k in data]

    def delete(self, key_id: str) -> None:
        """Delete a provider key. Returns None on success."""
        self._client.request("DELETE", f"/provider-keys/{key_id}")
