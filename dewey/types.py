"""Dataclass types for the Dewey API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Union


# ── Collections ───────────────────────────────────────────────────────────────


@dataclass
class Collection:
    id: str
    projectId: str
    name: str
    visibility: Literal["private", "public"]
    chunkSize: int
    chunkOverlap: int
    embeddingModel: str
    description: Optional[str]
    descriptionDocCount: Optional[int]
    enableSummarization: bool
    enableCaptioning: bool
    llmModel: Optional[str]
    lastSummarizationModel: Optional[str]
    lastCaptioningModel: Optional[str]
    instructions: Optional[str]
    createdAt: str
    deletedAt: Optional[str]

    @staticmethod
    def from_dict(d: dict) -> "Collection":
        return Collection(
            id=d["id"],
            projectId=d["projectId"],
            name=d["name"],
            visibility=d["visibility"],
            chunkSize=d["chunkSize"],
            chunkOverlap=d["chunkOverlap"],
            embeddingModel=d["embeddingModel"],
            description=d.get("description"),
            descriptionDocCount=d.get("descriptionDocCount"),
            enableSummarization=d.get("enableSummarization", True),
            enableCaptioning=d.get("enableCaptioning", True),
            llmModel=d.get("llmModel"),
            lastSummarizationModel=d.get("lastSummarizationModel"),
            lastCaptioningModel=d.get("lastCaptioningModel"),
            instructions=d.get("instructions"),
            createdAt=d["createdAt"],
            deletedAt=d.get("deletedAt"),
        )


# ── Documents ─────────────────────────────────────────────────────────────────

DocumentStatus = Literal[
    "pending", "uploading", "processing", "sectioned", "embedded", "ready", "error"
]


@dataclass
class Document:
    id: str
    collectionId: str
    filename: str
    storageKey: str
    markdownStorageKey: Optional[str]
    status: str
    fileSizeBytes: Optional[int]
    markdownFileSizeBytes: Optional[int]
    sectionCount: Optional[int]
    chunkCount: Optional[int]
    contentHash: Optional[str]
    errorMessage: Optional[str]
    createdAt: str

    @staticmethod
    def from_dict(d: dict) -> "Document":
        return Document(
            id=d["id"],
            collectionId=d["collectionId"],
            filename=d["filename"],
            storageKey=d["storageKey"],
            markdownStorageKey=d.get("markdownStorageKey"),
            status=d["status"],
            fileSizeBytes=d.get("fileSizeBytes"),
            markdownFileSizeBytes=d.get("markdownFileSizeBytes"),
            sectionCount=d.get("sectionCount"),
            chunkCount=d.get("chunkCount"),
            contentHash=d.get("contentHash"),
            errorMessage=d.get("errorMessage"),
            createdAt=d["createdAt"],
        )


@dataclass
class UploadUrlResponse:
    documentId: str
    uploadUrl: Optional[str]
    document: Optional[Document]

    @staticmethod
    def from_dict(d: dict) -> "UploadUrlResponse":
        doc_data = d.get("document")
        return UploadUrlResponse(
            documentId=d["documentId"],
            uploadUrl=d.get("uploadUrl"),
            document=Document.from_dict(doc_data) if doc_data else None,
        )


# ── Sections ──────────────────────────────────────────────────────────────────


@dataclass
class Section:
    id: str
    documentId: str
    title: str
    level: int
    summary: Optional[str]
    summaryType: Optional[str]
    position: int
    chunkCount: int
    markdownOffsetStart: int
    markdownOffsetEnd: int
    content: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> "Section":
        return Section(
            id=d["id"],
            documentId=d.get("documentId", ""),
            title=d["title"],
            level=d["level"],
            summary=d.get("summary"),
            summaryType=d.get("summaryType"),
            position=d["position"],
            chunkCount=d.get("chunkCount", 0),
            markdownOffsetStart=d.get("markdownOffsetStart", 0),
            markdownOffsetEnd=d.get("markdownOffsetEnd", 0),
            content=d.get("content"),
        )


# ── Chunks ────────────────────────────────────────────────────────────────────


@dataclass
class Chunk:
    id: str
    sectionId: str
    documentId: str
    collectionId: str
    content: str
    position: int
    tokenCount: int

    @staticmethod
    def from_dict(d: dict) -> "Chunk":
        return Chunk(
            id=d["id"],
            sectionId=d["sectionId"],
            documentId=d["documentId"],
            collectionId=d["collectionId"],
            content=d["content"],
            position=d["position"],
            tokenCount=d["tokenCount"],
        )


# ── Retrieval ─────────────────────────────────────────────────────────────────


@dataclass
class RetrievalChunk:
    id: str
    content: str
    position: int
    tokenCount: int

    @staticmethod
    def from_dict(d: dict) -> "RetrievalChunk":
        return RetrievalChunk(
            id=d["id"],
            content=d["content"],
            position=d["position"],
            tokenCount=d["tokenCount"],
        )


@dataclass
class RetrievalSection:
    id: str
    title: str
    level: int

    @staticmethod
    def from_dict(d: dict) -> "RetrievalSection":
        return RetrievalSection(id=d["id"], title=d["title"], level=d["level"])


@dataclass
class RetrievalDocument:
    id: str
    filename: str

    @staticmethod
    def from_dict(d: dict) -> "RetrievalDocument":
        return RetrievalDocument(id=d["id"], filename=d["filename"])


@dataclass
class RetrievalResult:
    score: float
    chunk: RetrievalChunk
    section: RetrievalSection
    document: RetrievalDocument

    @staticmethod
    def from_dict(d: dict) -> "RetrievalResult":
        return RetrievalResult(
            score=d["score"],
            chunk=RetrievalChunk.from_dict(d["chunk"]),
            section=RetrievalSection.from_dict(d["section"]),
            document=RetrievalDocument.from_dict(d["document"]),
        )


# ── Research ──────────────────────────────────────────────────────────────────


@dataclass
class ResearchSource:
    chunkId: str
    content: str
    sectionId: str
    sectionTitle: str
    sectionLevel: int
    documentId: str
    filename: str

    @staticmethod
    def from_dict(d: dict) -> "ResearchSource":
        return ResearchSource(
            chunkId=d["chunkId"],
            content=d["content"],
            sectionId=d["sectionId"],
            sectionTitle=d["sectionTitle"],
            sectionLevel=d["sectionLevel"],
            documentId=d["documentId"],
            filename=d["filename"],
        )


@dataclass
class ResearchEventToolCall:
    type: Literal["tool_call"]
    query: str
    tool: Optional[str]

    @staticmethod
    def from_dict(d: dict) -> "ResearchEventToolCall":
        return ResearchEventToolCall(
            type="tool_call",
            query=d["query"],
            tool=d.get("tool"),
        )


@dataclass
class ResearchEventChunk:
    type: Literal["chunk"]
    content: str

    @staticmethod
    def from_dict(d: dict) -> "ResearchEventChunk":
        return ResearchEventChunk(type="chunk", content=d["content"])


@dataclass
class ResearchEventDone:
    type: Literal["done"]
    sessionId: str
    sources: List[ResearchSource]

    @staticmethod
    def from_dict(d: dict) -> "ResearchEventDone":
        return ResearchEventDone(
            type="done",
            sessionId=d["sessionId"],
            sources=[ResearchSource.from_dict(s) for s in d.get("sources", [])],
        )


@dataclass
class ResearchEventError:
    type: Literal["error"]
    message: str

    @staticmethod
    def from_dict(d: dict) -> "ResearchEventError":
        return ResearchEventError(type="error", message=d["message"])


ResearchEvent = Union[
    ResearchEventToolCall,
    ResearchEventChunk,
    ResearchEventDone,
    ResearchEventError,
]


def research_event_from_dict(d: dict) -> ResearchEvent:
    t = d.get("type")
    if t == "tool_call":
        return ResearchEventToolCall.from_dict(d)
    if t == "chunk":
        return ResearchEventChunk.from_dict(d)
    if t == "done":
        return ResearchEventDone.from_dict(d)
    if t == "error":
        return ResearchEventError.from_dict(d)
    raise ValueError(f"Unknown research event type: {t!r}")


@dataclass
class ResearchResult:
    answer: str
    sessionId: str
    sources: List[ResearchSource]

    @staticmethod
    def from_dict(d: dict) -> "ResearchResult":
        return ResearchResult(
            answer=d["answer"],
            sessionId=d["sessionId"],
            sources=[ResearchSource.from_dict(s) for s in d.get("sources", [])],
        )


# ── Claims ────────────────────────────────────────────────────────────────────


@dataclass
class ClaimMapItem:
    id: str
    text: str
    documentId: str
    documentName: str
    sectionId: str
    sectionTitle: str
    importance: int
    x: float
    y: float
    sourceText: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> "ClaimMapItem":
        return ClaimMapItem(
            id=d["id"],
            text=d["text"],
            documentId=d["documentId"],
            documentName=d["documentName"],
            sectionId=d["sectionId"],
            sectionTitle=d["sectionTitle"],
            importance=d["importance"],
            x=d["x"],
            y=d["y"],
            sourceText=d.get("sourceText"),
        )


ClaimMapEvent = Union[
    # progress
    dict,
    # done / error — callers can check event["type"]
]


@dataclass
class Claim:
    id: str
    sectionTitle: str
    sectionLineage: str
    text: str
    importance: int
    position: int

    @staticmethod
    def from_dict(d: dict) -> "Claim":
        return Claim(
            id=d["id"],
            sectionTitle=d["sectionTitle"],
            sectionLineage=d.get("sectionLineage", ""),
            text=d["text"],
            importance=d["importance"],
            position=d["position"],
        )


@dataclass
class DocumentClaims:
    documentId: str
    claims: List[Claim]

    @staticmethod
    def from_dict(d: dict) -> "DocumentClaims":
        return DocumentClaims(
            documentId=d["documentId"],
            claims=[Claim.from_dict(c) for c in d.get("claims", [])],
        )


# ── Collection Stats ──────────────────────────────────────────────────────────


@dataclass
class CollectionStats:
    docCount: int
    totalFileSizeBytes: int
    totalSections: int
    totalChunks: int
    statusCounts: Dict[str, int]
    summarizedCount: int
    captionedCount: int
    claimsExtractedCount: int
    totalClaimsCount: int

    @staticmethod
    def from_dict(d: dict) -> "CollectionStats":
        return CollectionStats(
            docCount=d["docCount"],
            totalFileSizeBytes=d["totalFileSizeBytes"],
            totalSections=d["totalSections"],
            totalChunks=d["totalChunks"],
            statusCounts=d.get("statusCounts", {}),
            summarizedCount=d.get("summarizedCount", 0),
            captionedCount=d.get("captionedCount", 0),
            claimsExtractedCount=d.get("claimsExtractedCount", 0),
            totalClaimsCount=d.get("totalClaimsCount", 0),
        )


# ── Contradictions ────────────────────────────────────────────────────────────


@dataclass
class ContradictionClaimRef:
    id: str
    text: str
    sectionTitle: str
    documentId: str
    documentFilename: str

    @staticmethod
    def from_dict(d: dict) -> "ContradictionClaimRef":
        doc = d.get("document", {})
        return ContradictionClaimRef(
            id=d["id"],
            text=d["text"],
            sectionTitle=d.get("sectionTitle", ""),
            documentId=doc.get("id", ""),
            documentFilename=doc.get("filename", ""),
        )


@dataclass
class Contradiction:
    id: str
    severity: str
    status: str
    explanation: str
    suggestedInstruction: Optional[str]
    clusterTopicSummary: Optional[str]
    createdAt: str
    claims: List[ContradictionClaimRef]

    @staticmethod
    def from_dict(d: dict) -> "Contradiction":
        return Contradiction(
            id=d["id"],
            severity=d["severity"],
            status=d["status"],
            explanation=d["explanation"],
            suggestedInstruction=d.get("suggestedInstruction"),
            clusterTopicSummary=d.get("clusterTopicSummary"),
            createdAt=d["createdAt"],
            claims=[ContradictionClaimRef.from_dict(c) for c in d.get("claims", [])],
        )


@dataclass
class ContradictionList:
    total: int
    items: List[Contradiction]

    @staticmethod
    def from_dict(d: dict) -> "ContradictionList":
        return ContradictionList(
            total=d["total"],
            items=[Contradiction.from_dict(c) for c in d.get("items", [])],
        )


@dataclass
class ContradictionDetectResult:
    runId: str
    status: str
    enqueuedAt: str

    @staticmethod
    def from_dict(d: dict) -> "ContradictionDetectResult":
        return ContradictionDetectResult(
            runId=d["runId"],
            status=d["status"],
            enqueuedAt=d["enqueuedAt"],
        )


@dataclass
class ContradictionRun:
    id: str
    status: str
    claimsProcessed: Optional[int]
    clustersAnalyzed: Optional[int]
    contradictionsFound: Optional[int]
    model: Optional[str]
    startedAt: Optional[str]
    completedAt: Optional[str]
    error: Optional[str]
    createdAt: str

    @staticmethod
    def from_dict(d: dict) -> "ContradictionRun":
        return ContradictionRun(
            id=d["id"],
            status=d["status"],
            claimsProcessed=d.get("claimsProcessed"),
            clustersAnalyzed=d.get("clustersAnalyzed"),
            contradictionsFound=d.get("contradictionsFound"),
            model=d.get("model"),
            startedAt=d.get("startedAt"),
            completedAt=d.get("completedAt"),
            error=d.get("error"),
            createdAt=d["createdAt"],
        )


# ── Provider Keys ─────────────────────────────────────────────────────────────

ProviderName = Literal["openai", "cohere", "voyageai"]


@dataclass
class ProviderKey:
    id: str
    projectId: str
    provider: str
    name: str
    keyPreview: str
    createdAt: str

    @staticmethod
    def from_dict(d: dict) -> "ProviderKey":
        return ProviderKey(
            id=d["id"],
            projectId=d["projectId"],
            provider=d["provider"],
            name=d["name"],
            keyPreview=d["keyPreview"],
            createdAt=d["createdAt"],
        )
