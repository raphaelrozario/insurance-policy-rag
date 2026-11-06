from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVector

from app.schemas import SourceItem


SYSTEM_PROMPT = """You are an insurance policy research assistant.

Answer the user's question using only the supplied context.

Rules:
1. Do not use outside knowledge.
2. Cite supporting passages with labels such as [Source 1].
3. If the context is insufficient, clearly say that the available documents
   do not contain enough information.
4. Do not invent coverage decisions, exclusions, dates, limits, or procedures.
5. This is an informational assistant, not a final legal or claims decision.
"""


PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """Context:
{context}

Question:
{question}

Provide a concise answer with source citations.""",
        ),
    ]
)


def _format_context(documents: list[Document]) -> str:
    formatted_sections: list[str] = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "Unknown source")
        title = document.metadata.get("title", "Untitled")
        chunk_index = document.metadata.get("chunk_index", "unknown")

        formatted_sections.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Title: {title}",
                    f"Source: {source}",
                    f"Chunk: {chunk_index}",
                    document.page_content,
                ]
            )
        )

    return "\n\n".join(formatted_sections)


def answer_question(
    *,
    question: str,
    top_k: int,
    vector_store: PGVector,
    chat_model: ChatOpenAI,
) -> tuple[str, list[SourceItem]]:
    retriever = vector_store.as_retriever(
        search_kwargs={"k": top_k}
    )

    documents = retriever.invoke(question)

    if not documents:
        return (
            "The available documents do not contain enough information "
            "to answer this question.",
            [],
        )

    context = _format_context(documents)
    chain = PROMPT | chat_model | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    sources = [
        SourceItem(
            citation_number=index,
            source=str(document.metadata.get("source", "Unknown source")),
            title=document.metadata.get("title"),
            chunk_index=document.metadata.get("chunk_index"),
            preview=document.page_content[:300],
            metadata=document.metadata,
        )
        for index, document in enumerate(documents, start=1)
    ]

    return answer, sources
