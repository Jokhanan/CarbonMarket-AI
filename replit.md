# CarbonGPT — MVP

Modular carbon compliance analysis tool built with **Python 3.11 + FastAPI**.

## Architecture

```
carbongpt/
├── app/
│   ├── main.py          FastAPI app: /upload-document, /analyze, /analyze-with-template, /health
│   └── config.py        Centralised paths & env settings
├── core/
│   ├── models.py        Pydantic request/response types
│   └── orchestrator.py  Pipeline coordinator (docx → rules → response)
├── tools/
│   ├── parse_docx.py    Heading-based section extractor for .docx files
│   ├── section_mapper.py  Fuzzy heading normaliser & matcher (rapidfuzz)
│   └── rule_engine.py   YAML rule loader and evaluator (uses section_mapper)
├── rules/
│   └── goldstandard_mr_v1.yaml  GoldStandard MR compliance rules
└── tests/
    └── test_section_mapper.py   17 unit tests covering exact/fuzzy/missing
```

## Running the API

```bash
uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000
```

Interactive docs available at `http://localhost:3000/docs`.

## Running Tests

```bash
python -m pytest carbongpt/tests/ -v
```

## Endpoints

| Method | Path                     | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | /health                  | Liveness probe                                         |
| POST   | /upload-document         | Upload a .docx file, receive saved path                |
| POST   | /analyze                 | Analyse file against YAML rules (fuzzy matching)       |
| POST   | /analyze-with-template   | Compare file against a template doc's headings         |

## Tech Stack

- Python 3.11
- FastAPI 0.133
- Uvicorn 0.41
- python-docx 1.2
- PyYAML 6.0
- rapidfuzz (fuzzy string matching for section detection)
- python-multipart 0.0.22 (for file uploads)
- pytest (testing)

## Section Matching

The `section_mapper` module normalises headings (lowercase, remove punctuation,
collapse whitespace) and uses rapidfuzz `token_sort_ratio` with a configurable
threshold (default 85).  This means "B.1 Monitoring Period" correctly matches
the expected section "Monitoring Period".

## Extending the Rule Engine

To add a new rule type:
1. Write `_check_<type>(rule, sections, section_map) -> Finding | None` in `tools/rule_engine.py`
2. Register it in `_RULE_HANDLERS`

To add a new YAML rule set:
- Drop a `.yaml` file in `carbongpt/rules/`
- Pass its filename via the `rule_file` field in `POST /analyze`
