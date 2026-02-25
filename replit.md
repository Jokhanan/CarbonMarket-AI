# CarbonGPT — MVP

Modular carbon compliance analysis tool built with **Python 3.11 + FastAPI**.

## Architecture

```
carbongpt/
├── app/
│   ├── main.py            FastAPI: /upload-document, /analyze, /analyze-with-template, /health
│   └── config.py          Centralised paths & env settings
├── core/
│   ├── models.py          Pydantic request/response types (incl. compliance_score)
│   └── orchestrator.py    Pipeline coordinator (docx → rules → response)
├── tools/
│   ├── parse_docx.py      Heading-based section extractor for .docx files
│   ├── section_mapper.py  Fuzzy heading normaliser & matcher (rapidfuzz)
│   ├── rule_engine.py     YAML rule loader; supports required_section + required_field
│   └── regex_utils.py     Compiled regex pattern matcher for field detection
├── rules/
│   └── goldstandard_mr_v1.yaml  GoldStandard MR rules (7 sections + 5 fields)
└── tests/
    ├── test_section_mapper.py   17 tests (exact/fuzzy/missing sections)
    └── test_required_field.py   19 tests (field found/missing, section missing, score)
```

## Running the API

```bash
uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000
```

Interactive docs at `http://localhost:3000/docs`.

## Running Tests

```bash
python -m pytest carbongpt/tests/ -v
```

## Endpoints

| Method | Path                     | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | /health                  | Liveness probe                                         |
| POST   | /upload-document         | Upload a .docx file, receive saved path                |
| POST   | /analyze                 | Analyse file against YAML rules (sections + fields)    |
| POST   | /analyze-with-template   | Compare file against a template doc's headings         |

## Rule Types

| Type              | What it checks                                               |
|-------------------|--------------------------------------------------------------|
| required_section  | Heading exists in document (fuzzy match)                     |
| required_field    | Regex patterns match inside a section's body text            |

## Compliance Score

Starts at 100, decremented per finding: ERROR = -10, WARNING = -3, INFO = 0. Floor at 0.
Returned in both `/analyze` and `/analyze-with-template` responses.

## Tech Stack

- Python 3.11, FastAPI 0.133, Uvicorn 0.41
- python-docx 1.2, PyYAML 6.0, rapidfuzz, python-multipart
- pytest

## Extending the Rule Engine

1. Write `_check_<type>(rule, sections, section_map) -> Finding | None` in `tools/rule_engine.py`
2. Register in `_RULE_HANDLERS`
3. Add rules to any `.yaml` file in `carbongpt/rules/`
