from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from app.config import get_settings


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


@lru_cache
def get_vector_store() -> PGVector:
    settings = get_settings()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.pgvector_collection,
        connection=settings.database_url,
        use_jsonb=True,
    )


@lru_cache
def get_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
