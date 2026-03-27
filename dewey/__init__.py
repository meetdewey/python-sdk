"""Dewey Python SDK."""

from __future__ import annotations

from .client import DeweyError, DeweyHttpClient
from .resources.collections import CollectionsResource
from .resources.documents import DocumentsResource
from .resources.provider_keys import ProviderKeysResource
from .resources.research import ResearchResource
from .resources.retrieval import RetrievalResource
from .resources.sections import SectionsResource
from .resources.research import ResearchDepth
from .types import (
    Chunk,
    Collection,
    Document,
    DocumentStatus,
    ProviderKey,
    ProviderName,
    ResearchEvent,
    ResearchEventChunk,
    ResearchEventDone,
    ResearchEventError,
    ResearchEventToolCall,
    ResearchSource,
    RetrievalChunk,
    RetrievalDocument,
    RetrievalResult,
    RetrievalSection,
    Section,
    UploadUrlResponse,
)

__all__ = [
    "DeweyClient",
    "DeweyError",
    # Resources
    "CollectionsResource",
    "DocumentsResource",
    "SectionsResource",
    "RetrievalResource",
    "ResearchResource",
    "ProviderKeysResource",
    # Types
    "Collection",
    "Document",
    "DocumentStatus",
    "Section",
    "Chunk",
    "RetrievalResult",
    "RetrievalChunk",
    "RetrievalSection",
    "RetrievalDocument",
    "ResearchEvent",
    "ResearchEventToolCall",
    "ResearchEventChunk",
    "ResearchEventDone",
    "ResearchEventError",
    "ResearchSource",
    "ResearchDepth",
    "ProviderKey",
    "ProviderName",
    "UploadUrlResponse",
]


class DeweyClient:
    """
    Main entry point for the Dewey API.

    Usage::

        from dewey import DeweyClient

        client = DeweyClient(api_key="dwy_live_...")
        collections = client.collections.list()
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.meetdewey.com",
    ) -> None:
        self._http = DeweyHttpClient(api_key=api_key, base_url=base_url)

        #: Access and manage collections.
        self.collections = CollectionsResource(self._http)
        #: Upload and manage documents.
        self.documents = DocumentsResource(self._http)
        #: Browse sections and chunks.
        self.sections = SectionsResource(self._http)
        #: Hybrid semantic + keyword retrieval.
        self.retrieval = RetrievalResource(self._http)
        #: Agentic research via SSE streaming.
        self.research = ResearchResource(self._http)
        #: Manage provider API keys.
        self.provider_keys = ProviderKeysResource(self._http)
