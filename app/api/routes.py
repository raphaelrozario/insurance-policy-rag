from fastapi import APIRouter, Depends, HTTPException
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVector

from app.config import Settings, get_settings
from app.dependencies import get_chat_model, get_vector_store
from app.schemas import (
    IngestResponse,
    QueryRequest,
    QueryResponse,
    TextIngestRequest,
    WebIngestRequest,
)
from app.services.ingestion import ingest_text, ingest_web_page
from app.services.rag import answer_question


router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@router.post("/documents/web", response_model=IngestResponse)
def add_web_document(
    request: WebIngestRequest,
    vector_store: PGVector = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    try:
        document_id, loaded_count, chunk_count = ingest_web_page(
            url=str(request.url),
            css_classes=request.css_classes,
            document_type=request.document_type,
            vector_store=vector_store,
            settings=settings,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Web ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        source=str(request.url),
        documents_loaded=loaded_count,
        chunks_stored=chunk_count,
        document_id=document_id,
    )


@router.post("/documents/text", response_model=IngestResponse)
def add_text_document(
    request: TextIngestRequest,
    vector_store: PGVector = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    try:
        document_id, loaded_count, chunk_count = ingest_text(
            source=request.source,
            title=request.title,
            text=request.text,
            document_type=request.document_type,
            vector_store=vector_store,
            settings=settings,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Text ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        source=request.source,
        documents_loaded=loaded_count,
        chunks_stored=chunk_count,
        document_id=document_id,
    )


@router.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    vector_store: PGVector = Depends(get_vector_store),
    chat_model: ChatOpenAI = Depends(get_chat_model),
) -> QueryResponse:
    try:
        answer, sources = answer_question(
            question=request.question,
            top_k=request.top_k,
            vector_store=vector_store,
            chat_model=chat_model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        ) from exc

    return QueryResponse(answer=answer, sources=sources)
