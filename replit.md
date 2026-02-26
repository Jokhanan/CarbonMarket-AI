# CarbonGPT — MVP

Modular carbon compliance analysis tool built with **Python 3.11 + FastAPI + Streamlit**.

## Architecture

```
carbongpt/
├── app/
│   ├── main.py            FastAPI: /upload-document, /analyze, /analyze-with-template, /analyze-selected, /health
│   └── config.py          Centralised paths & env settings
├── core/
│   ├── models.py          Pydantic request/response types (incl. compliance_score)
│   ├── orchestrator.py    Pipeline coordinator (docx → rules → response)
│   ├── ai_review.py       AI review logic (prompt building, OpenAI calls)
│   ├── ai_review_worker.py  Subprocess worker for async AI review
│   └── task_store.py      File-backed task store (/tmp/carbongpt_tasks/)
├── tools/
│   ├── parse_docx.py      Two-pass section extractor (heading styles + heuristic fallback)
│   ├── section_mapper.py  Fuzzy heading normaliser & matcher (rapidfuzz)
│   ├── rule_engine.py     YAML rule loader; 4 rule types supported
│   └── regex_utils.py     Compiled regex utils: pattern matching, date validation
├── templates/
│   ├── registry.yaml      Maps (standard, doc_type, version) → template + rules paths
│   ├── registry.py        Python loader for registry.yaml
│   └── goldstandard/
│       └── MR_v1_1.docx   Gold Standard MR template v1.1
├── rules/
│   └── goldstandard_mr_v1.yaml  GoldStandard MR rules (8 sections, 8 fields, 2 date, 2 N/A)
├── ui/
│   └── streamlit_app.py   Streamlit web UI for document analysis
└── tests/
    ├── test_section_mapper.py   17 tests (exact/fuzzy/missing sections)
    ├── test_required_field.py   31 tests (all rule types, score, end-to-end)
    ├── test_registry.py         10 tests (registry lookup, /analyze-selected)
    └── test_parse_docx.py       17 tests (heading styles, heuristic, tables, debug)
```

## Running

```bash
bash start_carbongpt.sh   # Starts FastAPI (port 3000) + Streamlit UI (port 5000)
python -m pytest carbongpt/tests/ -v  # Tests (133 total)
```

## Endpoints

| Method | Path                     | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | /health                  | Liveness probe                                         |
| POST   | /upload-document         | Upload a .docx file, receive saved path                |
| POST   | /analyze                 | Analyse file against YAML rules (all rule types)       |
| POST   | /analyze-with-template   | Compare file against a user-supplied template           |
| POST   | /analyze-selected        | Analyse using internally registered template + rules   |
| POST   | /ai-review               | Start async AI review task, returns {task_id, status}  |
| GET    | /ai-review/{task_id}     | Poll AI review task status and results                 |
| GET    | /debug/sections?path=... | Diagnose section detection (raw paragraphs + markers)  |

## Template Registry

Templates are stored internally and selected by Standard + Document Type + Version.
Registry defined in `carbongpt/templates/registry.yaml`.  Users do NOT upload templates.

## Rule Types

| Type                                | What it checks                                                      |
|-------------------------------------|---------------------------------------------------------------------|
| required_section                    | Heading exists in document (fuzzy match)                            |
| required_field                      | Regex patterns match inside a section's body text                   |
| date_format_ddmmyyyy                | Dates in a section use DD/MM/YYYY (not YYYY-MM-DD or DD-MM-YYYY)   |
| not_applicable_required_when_blank  | Short sections (<N chars) must contain "N/A" or "Not Applicable"   |
| must_mention_keywords               | Section text must mention N of M keywords (case-insensitive)       |

## Compliance Score

Starts at 100, decremented per finding: ERROR = -10, WARNING = -3, INFO = 0. Floor at 0.

## Compliance Status (3-tier)

| Status | Label                    | Condition                                                         |
|--------|--------------------------|-------------------------------------------------------------------|
| FAIL   | NOT READY FOR SUBMISSION | Any STRUCTURE or KEY_FIELDS finding with severity ERROR           |
| REVIEW | NEEDS REVIEW             | Any findings exist, but none are critical STRUCTURE/KEY_FIELDS    |
| PASS   | BASIC CHECKS PASSED      | No findings at all                                                |

## Finding Categories

| Category     | Rule types mapped                                  |
|--------------|----------------------------------------------------|
| STRUCTURE    | required_section                                   |
| KEY_FIELDS   | required_field                                     |
| FORMAT       | date_format_ddmmyyyy, not_applicable_required_when_blank |
| CONTENT_HINT | must_mention_keywords                              |

## Tech Stack

- Python 3.11, FastAPI 0.133, Uvicorn 0.41
- Streamlit (web UI)
- python-docx 1.2, PyYAML 6.0, rapidfuzz, python-multipart
- openai (for AI review)
- pytest

## AI Review (beta)

- Async task pattern: `POST /ai-review` returns `{task_id, status}`, poll `GET /ai-review/{task_id}` for results
- AI review runs in a **separate subprocess** (`ai_review_worker.py`) with `start_new_session=True` to survive workflow restarts
- Task state persisted to `/tmp/carbongpt_tasks/{task_id}.json` (file-backed, not in-memory)
- Uses OpenAI Chat Completions (gpt-4o-mini by default, override with `CARBONGPT_AI_MODEL` env var)
- Uses raw `requests` library (not openai SDK) for API calls to minimize memory overhead
- Guide registry: `carbongpt/guides/__init__.py` — dynamically loads guide modules by (standard, doc_type)
- Supported document types (Gold Standard):
  - **MR** (Monitoring Report): `gs_mr_perfcert_v1_2.py` — 22 subsections across 7 parent sections
  - **PDD** (Project Design Document v1.5): `gs_pdd_v1_5.py` — 26 subsections across 5 parent sections
  - **PoA-DD** (Programme of Activity DD v2.2): `gs_poa_dd_v2_2.py` — 16 subsections across 5 parent sections
  - **VPA-DD** (VPA Design Document v2.3): `gs_vpa_dd_v2_3.py` — 27 subsections across 6 parent sections
- Per-subsection review: completeness_score, issues, suggested_fixes, questions_for_user
- Global summary: overall_risk (LOW/MEDIUM/HIGH), top_issues, top_actions, coherence_flags
- Safety: model never invents numbers; marks drafts with [DRAFT]; asks questions for missing info
- UI: Streamlit toggle "AI Review (beta)" with progress bar + polling; handles server restarts gracefully
- Task store persists standard + doc_type per task for correct guide selection

## Extending the Rule Engine

1. Write `_check_<type>(rule, sections, section_map) -> Finding | None` in `tools/rule_engine.py`
2. Register in `_RULE_HANDLERS`
3. Add rules to any `.yaml` file in `carbongpt/rules/`
