# Project Milestones

## Milestone 1 — Working baseline

- [x] Ingest raw text
- [x] Ingest selected webpage sections
- [x] Split documents into chunks
- [x] Generate embeddings
- [x] Persist chunks, metadata, and embeddings in PostgreSQL + pgvector
- [x] Retrieve top-k chunks using vector similarity
- [x] Generate an answer using retrieved context
- [x] Return citations and source metadata
- [x] Dockerize the API and PostgreSQL database
- [x] Verify ingestion, persistence, retrieval, and generation end-to-end
- [x] Add basic API health test

## Milestone 2 — PDF ingestion and usable application

- [ ] Add PDF upload endpoint
- [ ] Parse PDF pages into LangChain Documents
- [ ] Preserve filename, page number, source, and document metadata
- [ ] Reuse the existing chunking and embedding pipeline
- [ ] Return page-aware citations
- [ ] Test querying an uploaded insurance policy PDF
- [ ] Build Angular frontend for document upload and policy Q&A

## Milestone 3 — Measurable retrieval and answer quality

- [ ] Create a curated evaluation dataset of at least 30 question-to-source test cases
- [ ] Include answerable and intentionally unanswerable questions
- [ ] Log retrieved chunk IDs, ranks, and similarity scores
- [ ] Calculate Recall@1, Recall@3, Recall@5, and MRR
- [ ] Measure groundedness / faithfulness of generated answers
- [ ] Detect unsupported claims such as "not mentioned" being interpreted as "not covered"
- [ ] Compare chunk sizes and overlap values
- [ ] Add a relevance threshold
- [ ] Establish baseline evaluation results before retrieval improvements

## Milestone 4 — Better retrieval

- [ ] Add PostgreSQL full-text search
- [ ] Combine lexical and vector retrieval
- [ ] Add Reciprocal Rank Fusion (RRF)
- [ ] Add a reranker
- [ ] Compare vector-only vs hybrid retrieval
- [ ] Measure improvements against the same fixed evaluation dataset
- [ ] Tune top-k, relevance thresholds, and reranking depth using evaluation results

## Milestone 5 — Document lifecycle

- [ ] Store original uploaded files
- [ ] Track ingestion status
- [ ] Add document listing and retrieval
- [ ] Add delete operation
- [ ] Add update and re-index operations
- [ ] Detect duplicate documents
- [ ] Track document versions
- [ ] Make ingestion idempotent where appropriate

## Milestone 6 — Reliability and model-change safety

- [ ] Add request timeouts
- [ ] Add retry policies with exponential backoff
- [ ] Handle OpenAI 429 and 5xx failures gracefully
- [ ] Handle database and retrieval failures explicitly
- [ ] Separate model/provider configuration from application logic
- [ ] Version prompts
- [ ] Create regression tests for prompt and model changes
- [ ] Run evaluation tests in CI
- [ ] Fail CI when important quality metrics regress beyond an allowed threshold

## Milestone 7 — Observability and auditability

- [ ] Add structured logging
- [ ] Add request / trace IDs
- [ ] Trace retrieval, reranking, prompt construction, and LLM calls
- [ ] Record model name and prompt version
- [ ] Track latency by pipeline stage
- [ ] Track token usage and API cost
- [ ] Log retrieved source IDs for debugging and auditing
- [ ] Add basic latency / error / usage dashboards

## Milestone 8 — Security and multi-tenancy

- [ ] Authentication
- [ ] Add tenant and user IDs to document metadata
- [ ] Enforce authorization filters during retrieval
- [ ] Add prompt-injection defenses
- [ ] Validate uploaded file types and file sizes
- [ ] Protect secrets and API keys
- [ ] Redact sensitive information from logs where necessary
- [ ] Add audit logs
- [ ] Define basic data-retention behavior

## Milestone 9 — CI/CD and deployment

- [ ] Add GitHub Actions for unit tests
- [ ] Add evaluation suite to CI
- [ ] Build and validate Docker images in CI
- [ ] Add deployment workflow
- [ ] Deploy API, PostgreSQL/pgvector, and Angular frontend
- [ ] Configure production secrets securely
- [ ] Add production health checks
- [ ] Verify rollback / recovery path