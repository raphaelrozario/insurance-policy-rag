from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime

import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _build_splitter(settings: Settings) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )


def _prepare_chunks(
    documents: list[Document],
    *,
    source: str,
    document_type: str,
    settings: Settings,
) -> tuple[str, list[Document], list[str]]:
    document_id = _stable_hash(source)
    chunks = _build_splitter(settings).split_documents(documents)
    ingested_at = datetime.now(UTC).isoformat()

    chunk_ids: list[str] = []

    for index, chunk in enumerate(chunks):
        chunk_id = _stable_hash(
            f"{document_id}:{index}:{chunk.page_content}"
        )
        chunk_ids.append(chunk_id)

        chunk.metadata.update(
            {
                "document_id": document_id,
                "chunk_id": chunk_id,
                "chunk_index": index,
                "document_type": document_type,
                "source": chunk.metadata.get("source", source),
                "ingested_at": ingested_at,
            }
        )

    return document_id, chunks, chunk_ids


def ingest_web_page(
    *,
    url: str,
    css_classes: list[str] | None,
    document_type: str,
    vector_store: PGVector,
    settings: Settings,
) -> tuple[str, int, int]:
    # WebBaseLoader reads USER_AGENT from the environment.
    os.environ.setdefault("USER_AGENT", settings.user_agent)

    loader_arguments: dict = {"web_paths": (url,)}

    if css_classes:
        loader_arguments["bs_kwargs"] = {
            "parse_only": bs4.SoupStrainer(
                class_=tuple(css_classes)
            )
        }

    loader = WebBaseLoader(**loader_arguments)
    documents = loader.load()

    document_id, chunks, chunk_ids = _prepare_chunks(
        documents,
        source=url,
        document_type=document_type,
        settings=settings,
    )

    if chunks:
        # Deterministic IDs make repeated ingestion idempotent: matching IDs
        # are overwritten instead of creating duplicate chunks.
        vector_store.add_documents(
            documents=chunks,
            ids=chunk_ids,
        )

    return document_id, len(documents), len(chunks)


def ingest_text(
    *,
    source: str,
    title: str,
    text: str,
    document_type: str,
    vector_store: PGVector,
    settings: Settings,
) -> tuple[str, int, int]:
    document = Document(
        page_content=text,
        metadata={
            "source": source,
            "title": title,
        },
    )

    document_id, chunks, chunk_ids = _prepare_chunks(
        [document],
        source=source,
        document_type=document_type,
        settings=settings,
    )

    if chunks:
        vector_store.add_documents(
            documents=chunks,
            ids=chunk_ids,
        )

    return document_id, 1, len(chunks)
