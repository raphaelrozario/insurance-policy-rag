# Insurance Policy RAG

This project is a small Retrieval-Augmented Generation (RAG) application for asking questions about insurance policy content.

I built the first version mainly to understand the complete RAG flow instead of only using a framework at a high level. The backend currently supports ingesting raw text and selected webpage content, splitting that content into chunks, generating embeddings, storing those embeddings in PostgreSQL with `pgvector`, retrieving relevant chunks for a question, and using those chunks as context for an LLM-generated answer.

The project is still being extended. The current version is the working baseline that I will use for later experiments around PDF ingestion, retrieval evaluation, hybrid search, reranking, observability, reliability, and security.

---

## Current architecture

The current flow looks like this:

```text
Policy text / Web page
        |
        v
Document loader
        |
        v
LangChain Documents
        |
        v
RecursiveCharacterTextSplitter
        |
        v
OpenAI embeddings
        |
        v
PostgreSQL + pgvector
        |
        v
Vector similarity retrieval
        |
        v
Top-k relevant chunks
        |
        v
Prompt containing retrieved context + user question
        |
        v
Chat model
        |
        v
Answer + source metadata
```

There are two main flows in the application:

### Ingestion flow

```text
Input document
    ↓
Create LangChain Document
    ↓
Split into chunks
    ↓
Attach metadata
    ↓
Generate embeddings
    ↓
Store text + vector + metadata in PostgreSQL
```

### Query flow

```text
User question
    ↓
Generate query embedding
    ↓
Search pgvector
    ↓
Retrieve nearest chunks
    ↓
Build context
    ↓
Send context + question to chat model
    ↓
Return answer + sources
```

---

## Technology used

The current version uses:

- Python
- FastAPI
- PostgreSQL
- pgvector
- LangChain
- OpenAI embeddings
- OpenAI chat models
- Pydantic
- Docker
- Docker Compose
- pytest
- httpx

---

## Project structure

```text
insurance-policy-rag-starter/
│
├── app/
│   ├── api/
│   │   └── routes.py
│   │
│   ├── services/
│   │   ├── ingestion.py
│   │   └── rag.py
│   │
│   ├── config.py
│   ├── dependencies.py
│   ├── main.py
│   └── schemas.py
│
├── data/
│   └── sample_policy.md
│
├── db/
│   └── init.sql
│
├── docs/
│   └── MILESTONES.md
│
├── scripts/
│   └── ingest_sample.py
│
├── tests/
│   └── test_health.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## What each part does

### `app/main.py`

This is the FastAPI application entry point.

It creates the FastAPI app and registers the API routes.

Uvicorn starts the application using:

```text
app.main:app
```

which means:

```text
app.main
```

is the Python module, and:

```text
app
```

is the FastAPI object inside that module.

---

### `app/config.py`

This file contains application configuration.

The settings are loaded using Pydantic settings and can be overridden through environment variables.

Examples include:

```text
OPENAI_API_KEY
OPENAI_CHAT_MODEL
OPENAI_EMBEDDING_MODEL
DATABASE_URL
PGVECTOR_COLLECTION
CHUNK_SIZE
CHUNK_OVERLAP
DEFAULT_TOP_K
```

The real values are kept in `.env`.

The repository contains `.env.example` only so another developer knows which values need to be configured.

The actual `.env` file is ignored by Git because it may contain secrets such as the OpenAI API key.

---

### `app/dependencies.py`

This file creates the external clients used by the application.

It currently creates:

- the OpenAI embedding client
- the PostgreSQL/pgvector vector store
- the OpenAI chat model

For example, the embedding object is created once and then reused.

The actual embedding operation happens later when documents are stored or when a question is searched.

During ingestion:

```text
vector_store.add_documents(...)
```

uses the configured embedding model internally to create document embeddings.

During retrieval:

```text
retriever.invoke(question)
```

uses the same embedding model internally to create a query embedding.

---

### `app/schemas.py`

This file contains the Pydantic request and response models used by the API.

The main models currently include:

- `TextIngestRequest`
- `WebIngestRequest`
- `IngestResponse`
- `QueryRequest`
- `QueryResponse`
- `SourceItem`

These models provide input validation and make the API contract explicit.

---

### `app/api/routes.py`

This file contains the HTTP endpoints.

The route layer is intentionally kept small.

It accepts the HTTP request, validates it using Pydantic, calls the appropriate service function, and returns the response.

Current endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Check whether the API is running |
| POST | `/api/v1/documents/text` | Ingest raw text |
| POST | `/api/v1/documents/web` | Ingest webpage content |
| POST | `/api/v1/query` | Ask a question against stored documents |

---

### `app/services/ingestion.py`

This file contains the ingestion logic.

It handles:

- creating LangChain `Document` objects
- splitting documents into chunks
- generating deterministic document IDs
- generating deterministic chunk IDs
- adding metadata
- storing documents in pgvector

A simplified version of the flow is:

```text
raw text
    ↓
Document(page_content, metadata)
    ↓
RecursiveCharacterTextSplitter
    ↓
chunk 0
chunk 1
chunk 2
...
    ↓
OpenAI embeddings
    ↓
PostgreSQL + pgvector
```

The project currently uses SHA-256-based deterministic IDs.

A document ID is derived from the source.

Each chunk gets its own ID based on information including:

```text
document ID
chunk index
chunk content
```

This makes chunk IDs reproducible for the same input.

---

## Chunking

The project currently uses:

```python
RecursiveCharacterTextSplitter
```

with configurable values for:

```text
CHUNK_SIZE
CHUNK_OVERLAP
```

Chunk overlap is used so that information near a chunk boundary is not completely separated from the neighboring chunk.

For example:

```text
Chunk 1:
...
Section 3
Section 4 beginning

Chunk 2:
Section 4 beginning
Section 4 remainder
```

Some repeated text between the two chunks is expected.

This will later be evaluated instead of simply choosing chunk sizes by intuition.

---

## PostgreSQL and pgvector

PostgreSQL is used as the main data store.

The `pgvector` extension adds support for storing and searching embedding vectors.

The database currently contains LangChain-managed tables such as:

```text
langchain_pg_collection
langchain_pg_embedding
```

The collection table stores information about the logical vector collection.

The embedding table stores each individual chunk.

Important columns include:

```text
id
collection_id
embedding
document
cmetadata
```

Conceptually, one row looks like:

```text
chunk ID
collection ID
embedding vector
original chunk text
JSON metadata
```

The vector is used to find relevant content.

The original document text is used as context for the LLM.

---

## Metadata

Each stored chunk includes metadata such as:

```text
title
source
document_id
chunk_id
chunk_index
document_type
start_index
ingested_at
```

Example:

```json
{
  "title": "Sample Homeowners Policy",
  "source": "synthetic-homeowners-policy-v1",
  "chunk_index": 0,
  "document_type": "insurance_policy"
}
```

This metadata is returned with query results so that retrieved information can be traced back to its source.

Later versions will extend this with page numbers, file names, tenant IDs, version information, and other document lifecycle data.

---

## Retrieval

At query time, the application creates a LangChain retriever from the pgvector store.

The basic flow is:

```python
documents = retriever.invoke(question)
```

The question is converted to an embedding internally.

That embedding is compared against the stored document embeddings.

The most similar chunks are returned.

The current version uses top-k retrieval.

This means the retriever returns the nearest available chunks even when some of them may not be strongly relevant.

That is an important limitation of the baseline.

For example, if the stored policy contains no earthquake coverage information and the user asks:

```text
Does the policy cover earthquake damage?
```

the retriever will still return the nearest chunks it can find.

That does not mean those chunks actually contain evidence about earthquakes.

Later versions will add:

- similarity scores
- relevance thresholds
- hybrid retrieval
- reranking

---

## Prompt and answer generation

Retrieved documents are formatted into a context block before being sent to the chat model.

The flow is approximately:

```python
documents = retriever.invoke(question)

context = format_context(documents)

answer = chain.invoke({
    "context": context,
    "question": question
})
```

Each retrieved source is labeled so that the model can reference it.

Example:

```text
[Source 1]
Title: Sample Homeowners Policy
Source: synthetic-homeowners-policy-v1
Chunk: 0

<retrieved policy text>
```

The prompt instructs the model to answer using the retrieved context rather than relying on unsupported information.

The API also returns the retrieved source metadata separately from the generated answer.

---

## Known grounding limitation

One useful issue found during testing involved an unanswerable question.

The question was:

```text
Does the policy cover earthquake damage?
```

The policy does not contain information about earthquake coverage.

The model correctly identified that earthquake coverage was not mentioned, but then made the stronger statement that earthquake damage was therefore not covered.

Those two statements are not equivalent.

```text
Not mentioned in the retrieved evidence
```

does not necessarily mean:

```text
Explicitly not covered by the policy
```

This is one of the cases that will be added to the evaluation dataset.

The desired behavior is closer to:

```text
The retrieved policy content does not provide enough information to determine
whether earthquake damage is covered.
```

This type of case is one reason evaluation is part of the project roadmap instead of treating visually reasonable answers as sufficient.

---

# Running the project

## Prerequisites

You need:

- Docker Desktop
- an OpenAI API key
- Git if you want to clone or contribute to the repository

You do not need PostgreSQL installed separately because PostgreSQL runs inside Docker.

---

## 1. Configure environment variables

Create a `.env` file from the example file.

On Linux/macOS:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`.

At minimum, provide:

```text
OPENAI_API_KEY=<your-api-key>
```

The current defaults use:

```text
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

The database URL uses the Docker Compose service name:

```text
db
```

instead of:

```text
localhost
```

because the API connects to PostgreSQL from inside another Docker container.

Inside Docker Compose:

```text
API container
     |
     | hostname = db
     v
PostgreSQL container
```

---

## 2. Start the application

From the project root:

```bash
docker compose up --build
```

This starts two main services:

```text
api
db
```

The database container uses PostgreSQL with pgvector installed.

The initialization script enables:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Once startup completes, the API should be available at:

```text
http://localhost:8000
```

---

## 3. Health check

Open:

```text
http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

---

## 4. Run tests

Run:

```bash
docker compose exec api python -m pytest
```

The current test suite contains a basic API health test.

The project uses:

```text
python -m pytest
```

rather than calling `pytest` directly because that correctly resolves the application package in the current Docker setup.

---

## 5. Ingest the sample insurance policy

The repository contains a small synthetic policy document:

```text
data/sample_policy.md
```

It is intentionally synthetic and does not contain private customer information.

Run:

```bash
docker compose exec api python scripts/ingest_sample.py
```

The script:

1. reads the sample policy file
2. sends an HTTP POST request to the FastAPI text-ingestion endpoint
3. waits for the backend to process the document
4. prints the API response

A successful response currently looks similar to:

```json
{
  "source": "synthetic-homeowners-policy-v1",
  "documents_loaded": 1,
  "chunks_stored": 2,
  "document_id": "15c55137c2de5e8cc19374d073f6fa67121492cbc8a165c50c6436f791dcc621"
}
```

The exact number of chunks may change if the chunk size or overlap is changed.

---

## 6. Ask a question

You can use Swagger UI:

```text
http://localhost:8000/docs
```

and call:

```text
POST /api/v1/query
```

Example body:

```json
{
  "question": "Does the policy cover sudden water damage from a burst supply pipe?",
  "top_k": 4
}
```

A successful response includes:

```json
{
  "answer": "...",
  "sources": [
    {
      "citation_number": 1,
      "source": "synthetic-homeowners-policy-v1",
      "title": "Sample Homeowners Policy",
      "chunk_index": 0,
      "preview": "...",
      "metadata": {}
    }
  ]
}
```

---

## PowerShell query example

On Windows PowerShell, the following is easier than using a Bash-style multiline `curl` command:

```powershell
$body = @{
    question = "Does the policy cover sudden water damage from a burst supply pipe?"
    top_k = 4
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## Bash / Linux / macOS query example

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Does the policy cover sudden water damage from a burst supply pipe?",
    "top_k": 4
  }'
```

---

## Example questions

Some useful questions for the included synthetic policy are:

```text
Is sudden water damage from a burst pipe covered?
```

```text
Is long-term seepage covered?
```

```text
What claim documentation should the insured provide?
```

```text
Can the automated assistant make a final coverage decision?
```

And an intentionally unsupported question:

```text
Does the policy cover earthquake damage?
```

The last question is useful for testing grounding behavior.

The desired behavior is to state that the available evidence is insufficient rather than inventing a coverage decision.

---

# Webpage ingestion

The application also supports loading webpage content.

Endpoint:

```text
POST /api/v1/documents/web
```

Example request:

```json
{
  "url": "https://lilianweng.github.io/posts/2023-06-23-agent/",
  "css_classes": [
    "post-content",
    "post-title",
    "post-header"
  ],
  "document_type": "public_reference"
}
```

When CSS classes are supplied, BeautifulSoup filtering is used so that only selected sections of the page are parsed.

Internally this uses:

```python
bs4.SoupStrainer
```

with LangChain's `WebBaseLoader`.

If CSS classes are not supplied, the loader processes the whole page.

---

# Inspecting the database

You can connect directly to PostgreSQL from the Docker container:

```bash
docker compose exec db psql -U rag_user -d rag_db
```

Inside `psql`, list extensions:

```sql
\dx
```

You should see the `vector` extension.

List tables:

```sql
\dt
```

The current LangChain tables include:

```text
langchain_pg_collection
langchain_pg_embedding
```

Inspect the collection table:

```sql
SELECT
    uuid,
    name,
    cmetadata
FROM langchain_pg_collection;
```

Inspect stored chunks without printing the full embedding vector:

```sql
SELECT
    id,
    collection_id,
    document,
    cmetadata
FROM langchain_pg_embedding;
```

To count chunks:

```sql
SELECT COUNT(*)
FROM langchain_pg_embedding;
```

Exit PostgreSQL with:

```text
\q
```

---

# Docker notes

To stop the project without deleting stored PostgreSQL data:

```bash
docker compose down
```

The PostgreSQL data is stored in a Docker volume.

That means the data remains available the next time the containers are started.

To intentionally remove the volume and reset the database:

```bash
docker compose down -v
```

Use `-v` carefully because it deletes the persisted database volume.

---

# Current limitations

This project is intentionally still a baseline.

Some known limitations are:

- only text and webpage ingestion are currently supported
- PDF upload has not yet been implemented
- retrieval currently uses vector similarity only
- there is no relevance threshold
- top-k retrieval can return weakly related chunks
- there is no reranker yet
- there is no formal RAG evaluation framework yet
- there is no authentication or authorization
- document versioning is not implemented
- prompt/model regressions are not automatically tested
- tracing and production metrics are not implemented yet
- the application is not currently deployed to a cloud environment

These are planned extensions rather than hidden limitations.

---

# Development roadmap

## Milestone 1 — Working baseline

Completed:

- [x] Raw-text ingestion
- [x] Selected webpage ingestion
- [x] Document chunking
- [x] OpenAI embeddings
- [x] PostgreSQL + pgvector persistence
- [x] Vector similarity retrieval
- [x] Grounded answer generation
- [x] Source metadata and citations
- [x] Dockerized API and database
- [x] Basic health test
- [x] End-to-end verification of ingestion and querying

---

## Milestone 2 — PDF ingestion and application UI

Planned:

- [ ] Add PDF upload endpoint
- [ ] Parse PDF pages
- [ ] Preserve filename and page metadata
- [ ] Reuse the existing chunking and embedding pipeline
- [ ] Return page-aware citations
- [ ] Test with insurance policy PDFs
- [ ] Build Angular frontend for upload and Q&A

---

## Milestone 3 — Retrieval and answer evaluation

Planned:

- [ ] Create at least 30 question-to-source evaluation cases
- [ ] Include answerable and unanswerable questions
- [ ] Record retrieved chunk IDs and ranks
- [ ] Record similarity scores
- [ ] Calculate Recall@1
- [ ] Calculate Recall@3
- [ ] Calculate Recall@5
- [ ] Calculate MRR
- [ ] Evaluate answer groundedness / faithfulness
- [ ] Compare chunk sizes
- [ ] Compare chunk overlap values
- [ ] Add a relevance threshold
- [ ] Establish baseline metrics

---

## Milestone 4 — Better retrieval

Planned:

- [ ] PostgreSQL full-text search
- [ ] Hybrid lexical + vector retrieval
- [ ] Reciprocal Rank Fusion
- [ ] Reranking
- [ ] Retrieval tuning
- [ ] Compare improvements against the same evaluation set

The goal here is to measure whether retrieval changes actually help rather than assuming a more complicated pipeline is automatically better.

---

## Milestone 5 — Document lifecycle

Planned:

- [ ] Store original files
- [ ] Track ingestion state
- [ ] List documents
- [ ] Delete documents
- [ ] Re-index documents
- [ ] Detect duplicates
- [ ] Track document versions
- [ ] Make ingestion idempotent where appropriate

---

## Milestone 6 — Reliability and model-change safety

Planned:

- [ ] Request timeouts
- [ ] Retry policies
- [ ] Exponential backoff
- [ ] Graceful handling of OpenAI `429` errors
- [ ] Graceful handling of upstream `5xx` errors
- [ ] Explicit database failure handling
- [ ] Prompt versioning
- [ ] Model configuration abstraction
- [ ] Regression tests for prompt changes
- [ ] Regression tests for model migrations
- [ ] Run evaluation checks in CI

---

## Milestone 7 — Observability

Planned:

- [ ] Structured logs
- [ ] Request IDs
- [ ] Trace IDs
- [ ] Retrieval tracing
- [ ] Reranker tracing
- [ ] LLM call tracing
- [ ] Prompt version tracking
- [ ] Model version tracking
- [ ] Token usage
- [ ] API cost metrics
- [ ] Latency metrics
- [ ] Error metrics

The goal is to be able to understand exactly where a request failed or slowed down.

---

## Milestone 8 — Security

Planned:

- [ ] Authentication
- [ ] User and tenant metadata
- [ ] Authorization-aware retrieval
- [ ] Prompt-injection defenses
- [ ] File validation
- [ ] Upload size limits
- [ ] Secrets management
- [ ] Sensitive log redaction
- [ ] Audit logs
- [ ] Data retention rules

---

## Milestone 9 — CI/CD and deployment

Planned:

- [ ] GitHub Actions
- [ ] Run tests in CI
- [ ] Run RAG evaluation suite in CI
- [ ] Build Docker images in CI
- [ ] Production deployment workflow
- [ ] Cloud-hosted PostgreSQL/pgvector
- [ ] Secure production secrets
- [ ] Production health checks
- [ ] Basic rollback strategy

---

# Evaluation philosophy

One of the goals of this project is to avoid evaluating RAG systems only by manually reading a few responses.

For example, instead of saying:

```text
The reranker seems better.
```

the goal is to compare the same fixed evaluation set before and after the change.

Possible measurements include:

```text
Recall@k
MRR
answer groundedness
citation correctness
latency
token usage
cost
```

That will make decisions such as chunk size, retrieval strategy, reranking, and prompt changes measurable.

---

# Planned retrieval evolution

The current retrieval pipeline is:

```text
Question
    ↓
Vector search
    ↓
Top-k chunks
```

The planned version is:

```text
Question
    ↓
Vector retrieval
    +
PostgreSQL full-text retrieval
    ↓
Reciprocal Rank Fusion
    ↓
Reranker
    ↓
Relevance threshold
    ↓
Final context
    ↓
LLM
```

Each addition will be evaluated against the same test set.

---

# Why this project exists

I wanted this project to cover more than simply calling an LLM API.

The parts I am specifically using it to learn include:

- document ingestion
- embedding generation
- vector databases
- retrieval behavior
- metadata design
- prompt grounding
- citation handling
- RAG evaluation
- hybrid search
- reranking
- LLM regression testing
- API reliability
- observability
- security considerations
- CI/CD
- deployment

The current repository represents the first working version.

The next major feature is PDF ingestion, followed by a frontend and a proper evaluation framework.