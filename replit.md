# CarbonGPT — MVP

Modular carbon compliance analysis tool built with **Python 3.11 + FastAPI + Streamlit**.

## Architecture

```
carbongpt/
├── app/
│   ├── main.py            FastAPI: analysis + admin endpoints, DB init on startup
│   ├── admin_routes.py    Admin API: document CRUD, ingestion, semantic search
│   └── config.py          Centralised paths & env settings
├── core/
│   ├── models.py          Pydantic request/response types (incl. compliance_score)
│   ├── orchestrator.py    Pipeline coordinator (docx → rules → response)
│   ├── ai_review.py       AI review logic (prompt building, OpenAI calls)
│   ├── ai_review_worker.py  Subprocess worker for async AI review
│   ├── knowledge_retrieval.py  RAG: retrieves methodology/standard context from repo for AI review
│   └── task_store.py      File-backed task store (/tmp/carbongpt_tasks/)
├── repository/
│   ├── db.py              PostgreSQL connection manager (psycopg2)
│   ├── schema.py          DDL schema + seed data, auto-runs on startup
│   ├── store.py           CRUD operations for standards, documents, chunks, search
│   └── ingestion.py       Document parsing (PDF/DOCX), chunking, embeddings, auto-detect
├── guides/
│   ├── __init__.py        Guide registry: (standard, doc_type) → module loader
│   ├── gs_mr_perfcert_v1_2.py   Gold Standard MR guide (22 subsections)
│   ├── gs_pdd_v1_5.py          Gold Standard PDD guide (26 subsections)
│   ├── gs_poa_dd_v2_2.py       Gold Standard PoA-DD guide (16 subsections)
│   ├── gs_vpa_dd_v2_3.py       Gold Standard VPA-DD guide (27 subsections)
│   ├── vcs_pd_v4_4.py          Verra VCS-PD guide (36 subsections)
│   ├── vcs_mr_v4_4.py          Verra VCS-MR guide (28 subsections)
│   └── vcs_valver_v4_4.py      Verra VCS-ValVer guide (21 subsections)
├── tools/
│   ├── parse_docx.py      Two-pass section extractor (heading styles + heuristic fallback)
│   ├── section_mapper.py  Fuzzy heading normaliser & matcher (rapidfuzz)
│   ├── rule_engine.py     YAML rule loader; 5 rule types supported
│   └── regex_utils.py     Compiled regex utils: pattern matching, date validation
├── templates/
│   ├── registry.yaml      Maps (standard, doc_type, version) → template + rules paths
│   ├── registry.py        Python loader for registry.yaml
│   └── goldstandard/
│       └── MR_v1_1.docx   Gold Standard MR template v1.1
├── rules/
│   └── goldstandard_mr_v1.yaml  GoldStandard MR rules
├── ui/
│   ├── streamlit_app.py   Main Streamlit UI: Compliance Analyzer + Document Repository
│   └── admin_app.py       Standalone admin app (available on port 5001 if needed)
└── tests/
    ├── test_section_mapper.py   17 tests
    ├── test_required_field.py   31 tests
    ├── test_registry.py         10 tests
    └── test_parse_docx.py       17 tests
```

## Running

```bash
bash start_carbongpt.sh   # Starts FastAPI (port 3000) + Streamlit UI (port 5000)
python -m pytest carbongpt/tests/ -v  # Tests
```

## Endpoints

### Analysis Endpoints

| Method | Path                     | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | /health                  | Liveness probe                                         |
| POST   | /upload-document         | Upload a .docx file, receive saved path                |
| POST   | /analyze                 | Analyse file against YAML rules                        |
| POST   | /analyze-with-template   | Compare file against a user-supplied template           |
| POST   | /analyze-selected        | Analyse using internally registered template + rules   |
| POST   | /ai-review               | Start async AI review task                             |
| GET    | /ai-review/{task_id}     | Poll AI review task status and results                 |
| GET    | /debug/sections?path=... | Diagnose section detection                             |

### Admin / Document Repository Endpoints

| Method | Path                                | Description                                       |
|--------|-------------------------------------|---------------------------------------------------|
| GET    | /admin/standards                    | List all standards                                |
| POST   | /admin/standards                    | Create a new standard                             |
| GET    | /admin/standard-versions            | List standard versions (optional filter)          |
| POST   | /admin/standard-versions            | Create a new standard version                     |
| POST   | /admin/documents/upload             | Upload document to repository (auto-ingest)       |
| GET    | /admin/documents                    | List documents (filter by category, version)      |
| GET    | /admin/documents/{id}               | Get document details                              |
| PATCH  | /admin/documents/{id}               | Update document metadata                          |
| DELETE | /admin/documents/{id}               | Delete document                                   |
| POST   | /admin/documents/{id}/reingest      | Re-run ingestion for a document                   |
| GET    | /admin/stats                        | Repository statistics                             |
| GET    | /admin/search?q=...&limit=N        | Semantic search across all embedded content       |

## Document Repository

PostgreSQL-backed document knowledge base with pgvector for semantic search.

### Database Schema
- **standards**: Carbon credit standards (Gold Standard, Verra VCS, etc.)
- **standard_versions**: Versioned standard releases (v4.4, v1.x, etc.)
- **documents**: Uploaded files with metadata, auto-detection results, ingestion status
- **document_sections**: Extracted sections from parsed documents
- **document_chunks**: Text chunks with 1536-dim vector embeddings (text-embedding-3-small)
- **document_references**: Cross-document links

### Document Categories
standard_text, methodology, guidance, tool, template, example_pdd, example_mr, example_fvr, example_valver, example_other, rule_update, other

### Ingestion Pipeline
1. Upload PDF/DOCX → saved to `document_repository/`
2. Parse → extract text + sections (pdfplumber for PDF, python-docx for DOCX)
3. Auto-detect → AI identifies standard, version, category, applicability (gpt-4o-mini)
4. Chunk → 500-token chunks with 50-token overlap (tiktoken cl100k_base)
5. Embed → OpenAI text-embedding-3-small (1536 dimensions)
6. Store → sections + chunks + embeddings in PostgreSQL
7. Search → cosine distance via pgvector `<=>` operator

## Template Registry

Templates are stored internally and selected by Standard + Document Type + Version.
Registry defined in `carbongpt/templates/registry.yaml`.

## AI Review (beta)

- Async task pattern: `POST /ai-review` → `GET /ai-review/{task_id}`
- Runs in separate subprocess (`ai_review_worker.py`)
- Task state persisted to `/tmp/carbongpt_tasks/`
- Uses OpenAI gpt-4o-mini (override with `CARBONGPT_AI_MODEL` env var)
- Standard-aware prompts (Gold Standard vs Verra VCS)
- Supported: Gold Standard (MR, PDD, PoA-DD, VPA-DD) + Verra (VCS-PD, VCS-MR, VCS-ValVer)

### Knowledge-Augmented Review (RAG)

When the document repository has embedded content, AI review automatically retrieves
relevant methodology and standard text from the repository for each section being reviewed.
This means the AI checks documents against BOTH template requirements AND methodology-specific
requirements (eligibility criteria, calculation methods, monitoring parameters, baseline
approach). The retrieval uses semantic search (cosine similarity) with a relevance threshold
of 0.55 cosine distance, pulling up to 8 candidates per section, filtered by standard,
capped at ~2000 tokens of context per section.

## Tech Stack

- Python 3.11, FastAPI, Uvicorn, Streamlit
- PostgreSQL + pgvector (semantic search)
- psycopg2-binary, pdfplumber, tiktoken
- python-docx, PyYAML, rapidfuzz
- OpenAI API (AI review + embeddings + auto-detection)
- pytest
