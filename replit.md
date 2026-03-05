# CarbonGPT — Technical Overview

## Overview

CarbonGPT is an AI-powered carbon intelligence platform designed for end-to-end carbon credit project development and verification. It streamlines the creation, review, and export of crucial project documents (PDDs, MRs, PoA-DDs, VPA-DDs, ValVer) compliant with Gold Standard (GS4GG) and Verra VCS standards. The platform offers AI-assisted drafting, automated compliance review, intelligence extraction from uploaded documents, a findings response assistant, and document export capabilities that fill official templates. It also provides carbon market intelligence and a project-context-aware ChatAI assistant for Q&A. CarbonGPT aims to accelerate and de-risk carbon project development by automating complex, compliance-heavy documentation processes.

## User Preferences

- Iterative development; ask before making major changes
- Detailed explanations preferred
- DO NOT modify: `carbongpt/tests/` or `carbongpt/ui/admin_app.py`
- No emoji in UI — text labels only
- No hardcoding: improvements through AI prompts and guide files only

## System Architecture

The CarbonGPT platform utilizes a Python-based backend with FastAPI and a Streamlit frontend. It employs a PostgreSQL database with the pgvector extension for vector search, and raw SQL for database interactions (no ORM).

**Frontend:**
The UI is a single Streamlit application (`streamlit_app.py`) communicating with the FastAPI backend via HTTP. It uses `st.session_state` for state management and a custom CSS design system for styling, prioritizing a clean, card-based layout with a teal brand color (`#0d9488`). The UI includes a project creation wizard, project-specific forms, document management, AI writing and review interfaces, and an export function. A global chat widget with text and voice input (via Web Speech API) provides project-contextual assistance.

**Backend:**
The FastAPI application organizes routes into project-specific and admin modules. It handles project CRUD, document uploads, AI intelligence extraction, drafting, review, findings response generation, and document export. Long-running AI review tasks are managed by a separate asynchronous worker process. Database schema is ensured on startup, and methodologies are seeded.

**AI & NLP:**
The core AI components leverage OpenAI's GPT models for language model inference and `text-embedding-3-small` for embeddings. AI functions include drafting document sections, generating full documents, providing section explanations, performing compliance audits, extracting narrative summaries, and structured data extraction. AI context assembly prioritizes compact summaries and uses a guide file system that defines document structures, formatting instructions, and template scaffolds for AI generation.

Key AI architecture features:
- **Adaptive model selection**: Complex sections (equations, parameter blocks, additionality, baseline) use gpt-4o; simple narrative sections use gpt-4o-mini. Retry-with-escalation if mini output is too short.
- **Project-level RAG**: Uploaded documents are chunked, embedded, and stored in `project_doc_chunks` table. Section writing uses semantic retrieval (hybrid vector+keyword search) instead of raw text concatenation.
- **Project Brief**: A 500-word consistent summary is auto-generated from intake data + document chunks and included in every section prompt for cross-section coherence.
- **Cross-section consistency validation**: After drafting, a validator analyzes all sections together to flag contradictions, missing fields, and inconsistencies.
- **Output validation**: Each generated section is checked against the guide's `must_include` items, with coverage scores and missing requirement flags.
- **Section complexity classification**: `COMPLEX_SECTION_IDS` and `COMPLEX_CONTENT_FORMATS` in `ai_writer.py` determine which model to use per section.

**Document Processing:**
PDFs are parsed with `pdfplumber`, Word documents with `python-docx`, and Excel exports with `openpyxl`. `rapidfuzz` is used for fuzzy matching. The system extracts text, detects sections, and applies AI for intelligence extraction which populates project intake forms. Document export involves filling official `.docx` templates with AI-generated content.

**Data Flow:**
User interactions in the Streamlit UI trigger HTTP requests to the FastAPI backend. The backend interacts with the PostgreSQL database (via `store.py` with raw SQL) and the OpenAI API. Responses update the Streamlit UI. Document uploads involve saving files, extracting text, parsing sections, and AI-driven intelligence extraction before populating project data. AI writing involves gathering project context, methodology parameters, and using guide files to generate section drafts. Document export loads official templates and inserts generated content.

## External Dependencies

-   **PostgreSQL:** Primary relational database.
-   **pgvector:** PostgreSQL extension for efficient vector similarity search.
-   **OpenAI API:** Utilized for Large Language Model (LLM) inference (GPT-4o-mini) and text embeddings (`text-embedding-3-small`).
-   **Serper.dev API:** Used for web search capabilities, particularly for methodology status verification.
-   **Verra REST API:** Integrated for fetching project metadata and methodology PDFs from the Verra registry.
-   **Gold Standard API:** Provides access to project data and document templates from the Gold Standard registry.
-   **UNFCCC/CDM resources:** External source for CDM methodology booklets and tools.