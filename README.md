# RAG FastAPI — User Manual Q&A

Modular RAG service that answers questions about a single PDF (`document/user_manual.pdf`) over a streamed SSE endpoint.

## Stack

- **API**: FastAPI + `sse-starlette`
- **Orchestration**: LangGraph state graph (retrieve → rerank → prepare prompt)
- **Vector DB**: Qdrant in local/embedded mode (file-backed, no daemon)
- **Parsing**: `pymupdf4llm` (PDF → Markdown with heading hierarchy + page numbers)
- **Embeddings**: OpenAI `text-embedding-3-small` (1536-dim)
- **LLM**: OpenAI `gpt-4o-mini`, streamed

Each pipeline stage sits behind a `Protocol` so it can be swapped without touching the rest.

## Layout

```
app/
├── main.py                # FastAPI app + lifespan
├── config.py              # pydantic-settings (env-driven)
├── api/routes/            # /health, /ask
├── ingestion/             # parse → chunk → embed → upsert
├── retrieval/             # embedder, vector store, retriever, reranker
├── generation/            # LLM, prompts, LangGraph
└── schemas/               # Chunk, Citation, request/response models

scripts/ingest.py          # one-shot CLI: PDF → Qdrant
data/qdrant/               # local Qdrant store (gitignored)
tests/                     # chunking, retrieval, /ask route
```

## Setup

Requires Python 3.11+. Installed as an editable package so `python -m scripts.ingest` and `uvicorn app.main:app` resolve.

```bash
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"

cp .env.example .env
# edit .env: set OPENAI_API_KEY
```

## Ingest the manual

```bash
python -m scripts.ingest document/user_manual.pdf
# parsed N blocks → N chunks → N points stored
```

Re-runs are idempotent (chunks have stable UUIDv5 IDs). Wipe with `rm -rf data/qdrant`.

## Run the server

```bash
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs
```

The server refuses to start if the Qdrant collection doesn't exist — ingest first.

## Ask a question

```bash
curl -N -X POST http://127.0.0.1:8000/ask \
    -H 'Content-Type: application/json' \
    -d '{"question": "What is the role of the Collect Agent?"}'
```

Or the included client:

```bash
python request.py
```

The `/ask` endpoint streams Server-Sent Events:

| event      | payload                              |
|------------|--------------------------------------|
| `citation` | list of `{chunk_id, page, section_path}` for the chunks the LLM was given |
| `token`    | one LLM token at a time              |
| `done`     | end of stream                        |
| `error`    | error message (terminal)             |

## Tests

```bash
pytest
```

Covers chunker shapes, Qdrant upsert/search round-trip, and the `/ask` SSE route (with the embedder + LLM mocked).

## Where to extend

The seams are the `Protocol` classes:

| To add…                        | Implement…                                                  |
|--------------------------------|-------------------------------------------------------------|
| Hybrid (BM25 + dense) search   | a new retriever class implementing `DenseRetriever`'s shape |
| Reranking                      | replace `PassthroughReranker` in `app/retrieval/reranker.py` |
| Other source formats           | new parser implementing `DocumentParser`                    |
| Agentic loops (rewrite, retry) | add nodes/edges in `app/generation/graph.py` and switch the route to `graph.astream_events` |
