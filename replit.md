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
│   └── orchestrator.py    Pipeline coordinator (docx → rules → response)
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
python -m pytest carbongpt/tests/ -v  # Tests (75 total)
```

## Endpoints

| Method | Path                     | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | /health                  | Liveness probe                                         |
| POST   | /upload-document         | Upload a .docx file, receive saved path                |
| POST   | /analyze                 | Analyse file against YAML rules (all rule types)       |
| POST   | /analyze-with-template   | Compare file against a user-supplied template           |
| POST   | /analyze-selected        | Analyse using internally registered template + rules   |
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

## Compliance Score

Starts at 100, decremented per finding: ERROR = -10, WARNING = -3, INFO = 0. Floor at 0.

## Tech Stack

- Python 3.11, FastAPI 0.133, Uvicorn 0.41
- Streamlit (web UI)
- python-docx 1.2, PyYAML 6.0, rapidfuzz, python-multipart
- pytest

## Extending the Rule Engine

1. Write `_check_<type>(rule, sections, section_map) -> Finding | None` in `tools/rule_engine.py`
2. Register in `_RULE_HANDLERS`
3. Add rules to any `.yaml` file in `carbongpt/rules/`
