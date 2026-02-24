# CarbonGPT — MVP

Modular carbon compliance analysis tool built with **Python 3.11 + FastAPI**.

## Architecture

```
carbongpt/
├── app/
│   ├── main.py          FastAPI app: /upload-document, /analyze, /health
│   └── config.py        Centralised paths & env settings
├── core/
│   ├── models.py        Pydantic request/response types
│   └── orchestrator.py  Pipeline coordinator (docx → rules → response)
├── tools/
│   ├── parse_docx.py    Heading-based section extractor for .docx files
│   └── rule_engine.py   YAML rule loader and evaluator
└── rules/
    └── goldstandard_mr_v1.yaml  GoldStandard MR compliance rules
```

## Running the API

```bash
uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000
```

Interactive docs available at `http://localhost:3000/docs`.

## Endpoints

| Method | Path                | Description                                      |
|--------|---------------------|--------------------------------------------------|
| GET    | /health             | Liveness probe                                   |
| POST   | /upload-document    | Upload a .docx file, receive saved path          |
| POST   | /analyze            | Analyse a previously-uploaded file against rules |

## Tech Stack

- Python 3.11
- FastAPI 0.133
- Uvicorn 0.41
- python-docx 1.2
- PyYAML 6.0
- python-multipart 0.0.22 (for file uploads)

## Extending the Rule Engine

To add a new rule type:
1. Write `_check_<type>(rule, sections) -> Finding | None` in `tools/rule_engine.py`
2. Register it in `_RULE_HANDLERS`

To add a new YAML rule set:
- Drop a `.yaml` file in `carbongpt/rules/`
- Pass its filename via the `rule_file` field in `POST /analyze`
