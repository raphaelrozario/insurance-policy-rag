from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class WebIngestRequest(BaseModel):
    url: HttpUrl
    css_classes: list[str] | None = Field(
        default=None,
        description=(
            "Optional HTML class names to retain. If omitted, the whole page "
            "is parsed."
        ),
    )
    document_type: str = "policy_reference"


class TextIngestRequest(BaseModel):
    source: str = Field(
        min_length=1,
        description="Logical source name, file name, or public identifier.",
    )
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    document_type: str = "insurance_policy"


class IngestResponse(BaseModel):
    source: str
    documents_loaded: int
    chunks_stored: int
    document_id: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=4, ge=1, le=20)


class SourceItem(BaseModel):
    citation_number: int
    source: str
    title: str | None = None
    chunk_index: int | None = None
    preview: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
