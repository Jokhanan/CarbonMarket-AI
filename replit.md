# CarbonGPT — Technical Overview

---

## 1. PROJECT OVERVIEW

CarbonGPT is an AI-powered carbon intelligence platform for carbon credit project development and verification. It provides end-to-end tooling for writing, reviewing, and exporting Project Design Documents (PDDs), Monitoring Reports (MRs), Programme of Activities Design Documents (PoA-DDs), Voluntary Project Activity Design Documents (VPA-DDs), and Validation/Verification Reports (ValVer) compliant with Gold Standard (GS4GG) and Verra VCS standards.

The platform's core value proposition:
- **AI-Assisted Document Writing:** Section-by-section drafting using methodology knowledge, project context, and template scaffolds extracted from official standard templates.
- **AI-Powered Document Review:** Automated compliance auditing that checks documents against standard requirements, cross-references with PDD content, and identifies missing parameters.
- **Intelligence Extraction:** Uploaded documents are analyzed by AI to extract structured data points (e.g., project coordinates, proponent details, emission factors) that auto-populate project setup forms.
- **Findings Response Assistant:** Parses VVB audit reports (CARs, CLs, FARs) and generates professional responses with PDD update recommendations.
- **Document Export:** Fills official Gold Standard and Verra Word templates with generated content, producing audit-ready documents.
- **Carbon Market Intelligence:** Dashboard with analytics on carbon projects synced from Verra and Gold Standard registries.
- **ChatAI Assistant:** A project-context-aware chat interface for carbon market Q&A.

---

## 2. TECH STACK

### Backend
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| Vector Search | pgvector (PostgreSQL extension) |
| ORM | Raw SQL via psycopg2-binary (no ORM) |

### Frontend
| Component | Technology |
|-----------|-----------|
| UI Framework | Streamlit 1.54+ |
| Styling | Custom CSS design system (CSS variables, Inter font) |
| Voice Input | Web Speech API (browser-native, via embedded JavaScript) |

### AI & NLP
| Component | Technology |
|-----------|-----------|
| LLM | OpenAI GPT-4o-mini (configurable via `CARBONGPT_AI_MODEL` env var) |
| Embeddings | OpenAI text-embedding-3-small |
| Tokenizer | tiktoken |

### Document Processing
| Component | Technology |
|-----------|-----------|
| PDF Parsing | pdfplumber |
| Word Documents | python-docx |
| Excel Export | openpyxl |
| Fuzzy Matching | rapidfuzz |

### External APIs
| Service | Purpose |
|---------|---------|
| OpenAI API | LLM inference and embeddings |
| Serper.dev API | Web search for methodology status verification |
| Verra REST API | Project metadata and methodology PDFs |
| Gold Standard API | Project data and document templates |
| UNFCCC/CDM resources | CDM methodology booklets and tools |

### Python Dependencies (pyproject.toml)
fastapi, openai, openpyxl, pdfplumber, pgvector, psycopg2-binary, pytest, python-docx, python-multipart, pyyaml, rapidfuzz, streamlit, tiktoken, uvicorn

### Runtime Environment
- NixOS (Replit) with nodejs-20, python-3.11, postgresql-16 modules
- Streamlit serves on port 5000 (exposed as port 80)
- FastAPI serves on port 3000

---

## 3. PROJECT STRUCTURE

```
carbongpt/
├── app/                          # FastAPI application layer
│   ├── main.py                   # FastAPI entry point, startup events, legacy routes
│   ├── project_routes.py         # All project-related API endpoints (1617 lines)
│   ├── admin_routes.py           # Admin/repository management endpoints
│   └── config.py                 # Application configuration
│
├── core/                         # Business logic and AI modules
│   ├── ai_writer.py              # AI section drafting, intelligence extraction, review (1170 lines)
│   ├── ai_review.py              # Asynchronous AI document review engine (396 lines)
│   ├── ai_review_worker.py       # Background worker process for async review tasks
│   ├── doc_exporter.py           # Word document template filling and export (1298 lines)
│   ├── findings_extractor.py     # VVB findings extraction from PDF reports (350 lines)
│   ├── calculation_engine.py     # Emission reduction calculation engine (293 lines)
│   ├── methodology_parser.py     # AI methodology parsing into structured format (506 lines)
│   ├── methodology_kb.py         # Methodology knowledge base management
│   ├── knowledge_retrieval.py    # RAG retrieval for AI context (173 lines)
│   ├── compliance_checker.py     # Rule-based compliance checking
│   ├── web_intelligence.py       # Web search integration (Serper.dev)
│   ├── orchestrator.py           # Multi-step AI workflow orchestration
│   ├── models.py                 # Pydantic models for core domain
│   └── task_store.py             # In-memory task tracking for async operations
│
├── repository/                   # Data access layer
│   ├── schema.py                 # PostgreSQL DDL (all CREATE TABLE statements) (355 lines)
│   ├── store.py                  # All database CRUD functions (1360 lines)
│   ├── db.py                     # Database connection management
│   ├── ingestion.py              # Document ingestion pipeline
│   ├── methodology_db.py         # Canonical methodology names database
│   ├── methodology_sync.py       # Methodology download and sync
│   └── project_sync.py           # Registry project synchronization
│
├── ui/                           # Streamlit frontend
│   ├── streamlit_app.py          # Main UI application (5847 lines)
│   └── admin_app.py              # Admin panel UI (DO NOT MODIFY)
│
├── guides/                       # AI writing guide files (section definitions per doc type)
│   ├── gs_pdd_v1_5.py            # Gold Standard PDD guide
│   ├── gs_mr_perfcert_v1_2.py    # Gold Standard MR guide
│   ├── gs_poa_dd_v2_2.py         # Gold Standard PoA-DD guide
│   ├── gs_vpa_dd_v2_3.py         # Gold Standard VPA-DD guide
│   ├── vcs_pd_v4_4.py            # Verra VCS PD guide
│   ├── vcs_mr_v4_4.py            # Verra VCS MR guide
│   └── vcs_valver_v4_4.py        # Verra VCS ValVer guide
│
├── templates/                    # Document templates and registry configs
│   ├── goldstandard/             # GS Word templates (.docx)
│   └── registry.py/yaml         # Registry sync configuration
│
├── rules/                        # YAML compliance rule definitions
│   └── goldstandard_mr_v1.yaml   # Gold Standard MR compliance rules
│
├── tools/                        # Utility modules
│   ├── parse_docx.py             # Word document parser
│   ├── section_mapper.py         # Section detection and mapping
│   ├── rule_engine.py            # YAML rule evaluation
│   └── regex_utils.py            # Text extraction helpers
│
└── tests/                        # Test suite (DO NOT MODIFY)

document_repository/              # Global document repository (PDFs, methodology docs)
uploads/                          # User-uploaded project documents
.streamlit/config.toml            # Streamlit server configuration
start_carbongpt.sh                # Startup script (Streamlit + FastAPI + worker)
```

### Key Files by Responsibility

| File | Lines | Responsibility |
|------|-------|---------------|
| `streamlit_app.py` | 5847 | Entire frontend UI (all pages, tabs, forms, chat widget) |
| `project_routes.py` | 1617 | All project API endpoints (35+ routes) |
| `store.py` | 1360 | Database CRUD (60+ functions) |
| `doc_exporter.py` | 1298 | Word template filling for all 7 document types |
| `ai_writer.py` | 1170 | AI drafting, intelligence extraction, section explanation |

---

## 4. APPLICATION ARCHITECTURE

### 4.1 Frontend Architecture

The frontend is a **single Streamlit application** (`streamlit_app.py`) that renders all UI. It communicates with the backend exclusively via HTTP requests to the FastAPI server.

- **Routing:** Two top-level pages selected via sidebar radio: "Workspace" and "Admin"
- **State Management:** Streamlit's `st.session_state` dictionary manages:
  - `selected_project_id` — currently open project
  - `chat_history` / `chat_open` — chat widget state
  - `active_tab` — current workspace tab
  - `confirm_delete_*`, `expand_*` — UI interaction state
- **Styling:** Custom CSS design system injected via `st.markdown(unsafe_allow_html=True)` with CSS custom properties (design tokens) for colors, shadows, radii, and transitions. Brand color: `--brand-primary: #0d9488` (teal).
- **API Communication:** A helper `_fetch(path, method, json, timeout)` function wraps all HTTP requests to `API_BASE` (default `http://localhost:3000`).

### 4.2 Backend Architecture

The backend is a **FastAPI application** with two router modules:

```
main.py (FastAPI app)
├── /projects/* → project_routes.py (ProjectRouter, prefix="/projects")
├── /admin/*    → admin_routes.py (AdminRouter, prefix="/admin")
└── Legacy routes: /upload-document, /analyze, /ai-review, /debug/sections
```

- **No ORM:** All database operations use raw SQL via psycopg2. The `store.py` module provides a function-based data access layer.
- **Startup Events:** On startup, `ensure_schema()` creates/migrates all tables, and `populate_methodologies_from_projects()` seeds the methodology database.
- **Async Worker:** `ai_review_worker.py` runs as a separate process for long-running AI review tasks, polling a task store.

### 4.3 Data Flow

```
User Action → Streamlit UI → HTTP Request → FastAPI Endpoint
    → store.py (SQL) → PostgreSQL
    → ai_writer.py / ai_review.py (OpenAI API)
    → Response → Streamlit UI update (st.rerun())
```

**Document Upload Flow:**
1. User uploads PDF/DOCX → `POST /projects/{id}/documents`
2. File saved to `uploads/` directory
3. Text extracted (pdfplumber or python-docx)
4. Sections detected and parsed
5. `extract_document_intelligence()` → markdown summary → `ai_extracted_summary`
6. `extract_structured_intelligence()` → structured JSON → `ai_extracted_data`
7. User reviews Intelligence Review panel → confirms/dismisses → populates `project_intake`

**AI Writing Flow:**
1. User clicks "Generate Draft" on a section → `POST /projects/{id}/write`
2. Backend gathers: project intake data, methodology parameters, uploaded doc context, parent project docs
3. Guide file provides section definition, format instructions, and template scaffold
4. `generate_section_draft()` calls OpenAI with full context
5. Draft stored in `project_write_sessions`, displayed in UI

**Document Export Flow:**
1. User clicks "Generate Document" → `POST /projects/{id}/generate-template`
2. `doc_exporter.py` loads the official `.docx` template for the standard/doc_type
3. AI-generated sections are inserted at the correct template positions
4. KPI tables filled, checkboxes ticked from project intake
5. Final `.docx` returned as download

### 4.4 API Structure

All project endpoints are prefixed with `/projects`. Full endpoint list:

**Methodology:**
- `GET /projects/methodologies` — List methodologies (filter by standard, category, search)
- `GET /projects/methodologies/categories` — List categories
- `GET /projects/methodologies/{code}` — Get methodology details
- `POST /projects/methodologies/populate` — Seed methodology database

**Project CRUD:**
- `GET /projects/` — List projects (filter by status)
- `POST /projects/` — Create project
- `GET /projects/{id}` — Get project details
- `PATCH /projects/{id}` — Update project
- `DELETE /projects/{id}` — Delete project
- `GET /projects/{id}/children` — List child projects (VPAs under PoA)

**Documents:**
- `POST /projects/{id}/documents` — Upload and parse document
- `DELETE /projects/{id}/documents/{doc_id}` — Delete document
- `PATCH /projects/{id}/documents/{doc_id}/ai-context` — Toggle AI context flag
- `POST /projects/{id}/documents/{doc_id}/extract-intelligence` — Re-extract intelligence

**Intelligence Review:**
- `GET /projects/{id}/intelligence-suggestions` — Get aggregated suggestions
- `POST /projects/{id}/intelligence-confirm` — Confirm suggestions into intake
- `POST /projects/{id}/intelligence-dismiss` — Dismiss suggestions

**AI Writing:**
- `GET /projects/{id}/sections` — Get document section structure
- `POST /projects/{id}/write` — Generate section draft
- `POST /projects/{id}/write-all` — Generate all sections
- `PATCH /projects/{id}/section-text` — Save/edit section text
- `POST /projects/{id}/explain` — Get section guidance
- `GET /projects/{id}/write-sessions` — Get drafting history

**Review:**
- `POST /projects/{id}/review/{doc_id}` — Review uploaded document
- `POST /projects/{id}/review-draft` — Review current drafts

**Findings:**
- `POST /projects/{id}/parse-findings-document` — Extract findings from VVB report
- `POST /projects/{id}/respond-to-finding` — Generate response to single finding
- `POST /projects/{id}/batch-respond-to-findings` — Generate batch responses

**Calculations & Export:**
- `GET /projects/{id}/methodology-data` — Get parsed methodology
- `POST /projects/{id}/parse-methodology` — Parse methodology document
- `POST /projects/{id}/calculate` — Run emission calculations
- `POST /projects/{id}/export-calculation` — Export calculations to Excel
- `POST /projects/{id}/generate-template` — Generate filled Word document

**Chat:**
- `POST /projects/chat` — AI assistant chat (project-context-aware)

---

## 5. UI STRUCTURE

### 5.1 Sidebar
- Brand header with "C" logo icon and "CarbonGPT" title
- Navigation radio: Workspace | Admin
- Footer with version and AI status indicator

### 5.2 Workspace — Home View (no project selected)

**Projects Tab:**
- Project list with styled cards showing: project name, type badge, standard badge (gold for GS, blue for Verra), country, methodology, status badge with colored dot
- Cards have left-border accent color by standard
- "New Project" button opens a multi-step creation wizard:
  - Step 1: Select project type (Standalone PDD, Monitoring Report, PoA-DD, VPA)
  - Step 2: Enter details (standard, name, methodology, country, parent linking)

**Carbon Intelligence Tab:**
- Global overview: total projects, estimated annual credits, distribution charts
- Country explorer: per-country analytics
- Methodology analysis: trends and statistics
- Project browser: searchable registry project list
- Sync controls: pull latest data from external registries

### 5.3 Workspace — Project View (project selected)

**Project Setup Tab:**
Two-layer intake form system:
- **Standard Layer:** Type-specific static forms. All start with Developer/Proponent card. PDD has 12+ cards covering project overview, crediting dates, technology, location, baseline/additionality, monitoring, emission reductions, SDGs, stakeholders, safeguards, plus standard-specific cards (GS: Prior Consideration & Financial Need; Verra: Legal & Compliance). PoA-DD adds management system, programme duration. VPA-DD adds crediting period, baseline scenario. MR adds implementation status, Forward Action Requests, calibration & data quality. ValVer has scope/assessment/findings.
- **Methodology Layer:** Dynamic fields rendered from `methodology_parsed.parsed_data` — methodology choices, calculation method selector, project-specific parameters, qualitative requirements, monitoring parameters with planned approaches, default values with override capability.
- Fields populated from intelligence show teal "from filename" source attribution labels.

**Documents Tab:**
- File upload area with smart prompts by project type
- Document cards grouped by category (core/supporting/other) with word count, AI context toggle
- "Extracted intelligence" expander showing markdown summary
- "Extract intelligence" button for documents without extraction
- **Intelligence Review section:** Expandable category cards with per-item Confirm/Dismiss buttons, conflict display for multiple source values, current value comparison, "Confirm all" per category

**Write / Draft Tab:**
- Section list from guide file with status indicators (drafted/empty)
- Per-section: "Generate Draft" button, "Explain Section" button, content editor
- "Generate All Sections" batch operation
- "AI Context" expander showing active documents and word counts
- "Review Draft" button to audit current drafts without export

**Review Tab:**
- Upload document for AI review
- Review results display with risk scores, compliance alerts, section-by-section analysis
- Polling UI for long-running review tasks

**Respond to Findings Tab:**
Three sub-tabs:
1. "Enter Findings Manually" — single finding form
2. "Upload Findings Document" — parse VVB report, select findings, batch generate responses
3. "Findings Intelligence" — knowledge base stats and common patterns for project methodology

**Export Tab:**
- Generate filled Word document for all supported doc types
- Download button for the generated `.docx`

### 5.4 Admin Page
- Upload Documents: ingest PDFs/DOCX into global repository
- Document Library: browse, re-ingest, delete repository files
- Semantic Search: natural language query across all ingested content
- Compliance Rules: manage AI compliance rules
- Web Intelligence: configure web monitoring agents
- Methodology Sync: download and parse methodologies
- Manage Standards: define/update supported carbon standards

### 5.5 Chat Widget (Global)
- Toggle button "AI Assistant" at bottom-right of every page
- Styled chat panel with brand header, scrollable message history
- Text input + Send/Clear buttons
- Voice input button using Web Speech API (browser-native)
- Project-context-aware: when a project is open, the assistant has access to project metadata, intake data, document intelligence, and drafted sections

---

## 6. FEATURES IMPLEMENTED

1. **Project Management:** Full CRUD for projects with 5 types (PDD, MR, PoA-DD, VPA-DD, ValVer), project hierarchy (PoA → VPA parent-child)
2. **Document Upload & Parsing:** PDF and DOCX upload with automatic text extraction, section detection, and parsing
3. **AI Intelligence Extraction:** Two-layer extraction (markdown summary + structured JSON) with field-level data points mapped to intake form schema
4. **Intelligence Review Layer:** Aggregated suggestions from all documents, grouped by category, confirm/dismiss workflow, source attribution tracking, no-overwrite policy with force override
5. **AI Section Drafting:** Per-section and full-document generation using guide files with template scaffolds, methodology context, and uploaded document context
6. **AI Document Review:** Compliance auditing with risk scores, section-by-section analysis, and PDD-MR cross-referencing
7. **Draft Review:** Review current drafts without needing to export first
8. **Findings Response Assistant:** Parse VVB audit reports, extract individual findings, generate professional responses with PDD update recommendations, batch processing, CSV/text export
9. **Document Export:** Fill official Gold Standard and Verra Word templates (7 doc types) with AI-generated content, KPI table filling, checkbox ticking
10. **Calculation Engine:** Emission reduction calculations from parsed methodologies with Excel export
11. **Methodology Knowledge Base:** 195 methodologies indexed, 4 priority methodologies with deep AI-extracted knowledge (equations, parameters, defaults, applicability)
12. **Methodology Parser:** AI-powered methodology parsing into structured calculation format
13. **Carbon Market Intelligence Dashboard:** Project analytics from Verra and Gold Standard registries with charts and country explorer
14. **Global Document Repository:** Admin-managed knowledge base with PDF/DOCX ingestion, semantic search (pgvector), and full-text search
15. **Compliance Rules Engine:** Database-driven rules with YAML definitions, admin management UI
16. **Web Intelligence:** Real-time web search integration for methodology status verification
17. **ChatAI Assistant:** Project-context-aware chat with text and voice input
18. **Premium CSS Design System:** Design tokens, dark sidebar, brand identity, card-based layouts, hover/elevation effects, responsive styling

---

## 7. FEATURES PARTIALLY IMPLEMENTED

1. **Methodology Calculation Engine:** The parser and calculation engine exist but are limited to the 4 priority methodologies. Non-priority methodologies lack deep parsed data for calculations.
2. **Web Intelligence Agents:** The infrastructure for web monitoring agents exists but is not fully automated (requires manual trigger).
3. **Registry Sync:** Project synchronization from Verra and Gold Standard registries works but is manually triggered; no scheduled auto-sync.
4. **Voice Input in Chat:** Uses Web Speech API which requires browser support (Chrome/Edge); the voice-to-text-to-submit flow relies on DOM manipulation of Streamlit's input elements, which can be fragile across Streamlit versions.

---

## 8. FEATURES NOT IMPLEMENTED YET

1. **User Authentication & Multi-tenancy:** No login system, no user accounts, no role-based access control. Currently single-user.
2. **Real-time Collaboration:** No multi-user editing or commenting on documents.
3. **Version History:** No document versioning or draft history tracking beyond the current write session.
4. **Notification System:** No alerts for methodology updates, compliance rule changes, or review completions.
5. **Advanced RAG Pipeline:** Embeddings and vector search exist in the schema but are not fully utilized in the AI writing pipeline (primarily uses direct text context rather than semantic retrieval).
6. **Automated Compliance Monitoring:** No scheduled checks against changing standard requirements.
7. **Template Editor:** No UI for customizing document templates or guide files.
8. **Batch Project Operations:** No bulk import/export of projects.
9. **API Authentication:** No API keys, OAuth, or rate limiting on the FastAPI endpoints.

---

## 9. DATA MODEL

### Core Tables

**`user_projects`** — User-created carbon projects
- `id` (serial PK), `name`, `standard` (GoldStandard/Verra), `doc_type`, `methodology`, `country`, `status`
- `project_type` (standalone_pdd, monitoring_report, poa_programme, vpa_component, valver_report)
- `parent_project_id` (self-referencing FK for PoA → VPA hierarchy)
- `project_settings` (JSONB) — methodology choices, calculation method, defaults
- `project_intake` (JSONB) — all form data organized by category (proponent, technology, location, etc.)
  - `project_intake._intelligence_sources` — tracks which fields were populated from document intelligence
  - `project_intake._dismissed_suggestions` — stores dismissed intelligence suggestions
- `crediting_period_start`, `crediting_period_years`, `monitoring_period_start`, `monitoring_period_end`

**`project_documents`** — Files uploaded per project
- `id` (serial PK), `project_id` (FK), `doc_type`, `file_name`, `file_path`, `status`
- `parsed_text` — extracted raw text
- `parsed_sections` (JSONB) — detected sections
- `ai_extracted_summary` (TEXT) — markdown intelligence summary
- `ai_extracted_data` (JSONB) — structured extraction: `[{category, field_key, value, confidence, source}]`
- `use_as_ai_context` (BOOLEAN) — whether to include in AI writing context
- `review_result` (JSONB) — AI review findings

**`project_write_sessions`** — AI writing progress per section
- `id` (serial PK), `project_id` (FK), `doc_type`, `section_id`, `section_title`
- `generated_text`, `user_text`, `status`
- `ai_context` (JSONB) — snapshot of context used for generation

### Knowledge Base Tables

**`documents`** — Global document repository
- Linked to `standard_versions` via FK
- `search_vector` (tsvector) for full-text search

**`document_chunks`** — Text chunks with embeddings
- `embedding` (vector(1536)) for semantic search via pgvector

**`methodology_knowledge`** — Extracted methodology intelligence
- Chunks tagged by type: equations, parameters, applicability, monitoring, leakage, quantification

**`methodology_parsed`** — Structured methodology data
- `parsed_data` (JSONB) — calculation methods, parameters, defaults

**`findings_knowledge`** — VVB findings knowledge base
- Finding type (CAR, CL, FAR), severity, PDD section, topic, resolution

### Supporting Tables
- `standards`, `standard_versions` — Carbon standard definitions
- `carbon_projects` — Registry-synced project data (Verra/GS)
- `compliance_rules` — Active compliance rules
- `document_sections`, `document_references` — Document structure
- `methodologies` — Methodology metadata (195 entries)
- `methodology_structure` — Section mapping of methodology documents

---

## 10. AI COMPONENT

### AI Functions (all in `ai_writer.py`)

| Function | Purpose | Output |
|----------|---------|--------|
| `_call_openai(system, user, format, max_tokens)` | Low-level OpenAI API wrapper | Raw completion text |
| `generate_section_draft(standard, doc_type, section_id, project_info, ...)` | Draft a document section | Formatted text following guide template scaffold |
| `generate_full_document(standard, doc_type, project_info)` | Orchestrate all-section generation | Dict of section_id → draft text |
| `explain_section(standard, doc_type, section_id)` | Training/guidance for a section | Plain-language explanation |
| `review_with_context(standard, doc_type, document_text, ...)` | Compliance audit | Structured JSON review with scores and issues |
| `extract_document_intelligence(parsed_text, file_name, doc_type)` | Narrative intelligence extraction | Markdown summary |
| `extract_structured_intelligence(parsed_text, file_name, doc_type)` | Field-level data extraction | JSON array: `[{category, field_key, value, confidence, source}]` |

### AI Context Assembly

The `_gather_ai_context()` function assembles context for AI operations:
1. Collects all documents where `use_as_ai_context=true`
2. Prefers `ai_extracted_summary` (compact) over raw text (truncated to 12K chars)
3. Pulls parent project documents for VPA/MR projects
4. Total context limit: 50K characters
5. PDD text for MR cross-referencing: up to 25K characters

### Guide File System

Seven guide files define document structure per standard/doc_type. Each guide contains:
- Section definitions with IDs, titles, and descriptions
- `content_format`: prose, table, parameter_blocks, checklist, equations_and_prose, summary_table
- `format_instructions`: specific formatting rules for the AI
- `template_scaffold`: exact table/block structure extracted from official templates
- `subsections`: nested section hierarchy

### INTAKE_FIELD_SCHEMA

Defines valid categories and field keys for structured intelligence extraction. Categories include: proponent, project_overview, technology, location, baseline_additionality, emission_reductions, monitoring, stakeholders, safeguards, prior_consideration, legal_compliance, monitoring_period, emission_factors, test_results. Each category has specific field keys (e.g., `proponent.organization_name`, `emission_factors.fnrb`).

### Model Configuration
- Default model: `gpt-4o-mini` (set via `CARBONGPT_AI_MODEL` env var)
- Embeddings: `text-embedding-3-small`
- Max tokens per request: 2000-16000 depending on function
- Temperature: 0.3 for drafting, 0.5 for chat, 0.2 for extraction

---

## 11. CURRENT LIMITATIONS

1. **Single-User System:** No authentication, authorization, or multi-tenancy. All data is shared.
2. **Streamlit UI Constraints:** Single-threaded execution model means all operations block the UI. No real-time updates without polling. State management via `st.session_state` doesn't persist across browser sessions.
3. **Large Monolithic UI File:** `streamlit_app.py` is 5847 lines, making maintenance and navigation difficult.
4. **No ORM:** Raw SQL throughout `store.py` increases risk of SQL injection (though parameterized queries are used) and makes schema changes labor-intensive.
5. **Limited Methodology Coverage:** Only 4 of 195 methodologies have deep AI-extracted knowledge. Non-priority methodologies lack parsed calculation data.
6. **AI Context Window Limits:** 50K character context limit means large projects with many documents may lose important context.
7. **No Caching Layer:** Every page load re-fetches all data from the API. No Redis or in-memory caching.
8. **Template Fragility:** Word template filling relies on exact heading styles and section markers. Template format changes from standards bodies can break export.
9. **Voice Input Browser Dependency:** Web Speech API only works in Chromium-based browsers.
10. **No Error Recovery:** Failed AI operations (timeouts, rate limits) require manual retry with no automatic retry logic.
11. **Deployment Gap:** The `.replit` deployment config points to a Node.js build (`dist/index.cjs`) but the actual app is Python. The deployment pipeline needs configuration for the Python/Streamlit stack.

---

## 12. NEXT DEVELOPMENT PRIORITIES

1. **User Authentication:** Add login system with role-based access (Admin, Developer, Reviewer). Essential for multi-user deployment.
2. **Performance Optimization:** Add caching layer (Redis or in-memory), paginate project/document lists, lazy-load AI results.
3. **UI Refactoring:** Break `streamlit_app.py` into modular page files. Consider migrating to a React frontend for richer interactivity.
4. **Methodology Expansion:** Automate the deep extraction pipeline to cover more of the 195 methodologies beyond the current 4 priority ones.
5. **RAG Enhancement:** Fully integrate vector search into the AI writing pipeline for more relevant context retrieval instead of concatenated text.
6. **Version Control:** Add document versioning and draft history so users can compare and revert changes.
7. **Deployment Configuration:** Set up proper Python deployment pipeline (Docker or Replit autoscale with Python runtime).
8. **API Security:** Add API key authentication, rate limiting, and input validation hardening.
9. **Automated Testing:** Expand test coverage for AI functions, API endpoints, and UI flows.
10. **Collaboration Features:** Multi-user editing, commenting, and review assignment workflows.

---

## User Preferences

- Iterative development; ask before making major changes
- Detailed explanations preferred
- DO NOT modify: `carbongpt/tests/` or `carbongpt/ui/admin_app.py`
- No emoji in UI — text labels only
- No hardcoding: improvements through AI prompts and guide files only

## External Dependencies

- **PostgreSQL:** Primary database (DATABASE_URL env var)
- **pgvector:** PostgreSQL extension for semantic search
- **OpenAI API:** LLM and embeddings (OPENAI_API_KEY env var)
- **Serper.dev API:** Web search (SERPER_API_KEY env var)
- **Verra APIs:** Methodology PDFs and project metadata
- **Gold Standard API:** Project data and templates
- **UNFCCC/CDM:** CDM methodology resources
