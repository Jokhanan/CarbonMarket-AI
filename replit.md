# CarbonGPT — MVP

## Overview

CarbonGPT is a modular compliance analysis tool designed to streamline and automate carbon credit project development and verification. It provides a comprehensive platform for managing, analyzing, and ensuring compliance of carbon projects against various international standards such as Gold Standard and Verra VCS. The project aims to reduce manual effort, minimize errors, and accelerate the validation and verification process. By leveraging AI, web intelligence, and a robust document repository, CarbonGPT enhances efficiency, accuracy, and transparency in the carbon market, contributing to faster climate action and improved project quality.

## User Preferences

I want iterative development. Ask before making major changes. I prefer detailed explanations. Do not make changes to the folder `carbongpt/tests/`. Do not make changes to the file `carbongpt/ui/admin_app.py`.

## System Architecture

CarbonGPT is built with Python 3.11, FastAPI for backend services, and Streamlit for the user interface.

**UI/UX Decisions:**
The application features a streamlined two-section navigation:
- **Workspace (Streamlit UI):** Contains "My Projects" (project workspace) and "Carbon Intelligence" (dashboard with project data from Verra and Gold Standard registries).
- **Project Workspace Tabs:** Focus on document writing and review: "Project Setup" (guided intake form), "Write / Draft" (AI writing assistant), "Review" (AI-powered document review), "Export" (Word/Excel).
- **Project Intake Form:** A 9-card guided form for collecting project data, stored in a `project_intake` JSONB column.
- **Admin (Streamlit UI):** Document repository management, compliance rules, knowledge base, methodology sync, and web intelligence tools.

**Technical Implementations:**

-   **Document Processing:** Uses `pdfplumber` and `python-docx` for parsing. Documents undergo classification (filename, keyword, AI), chunking (`tiktoken`), and embedding (`OpenAI text-embedding-3-small`).
-   **AI Review System (beta):** An asynchronous process (`ai_review_worker.py`) for AI-powered document review using `gpt-4o-mini`, supporting knowledge-augmented retrieval (RAG).
-   **Compliance Rules Engine:** A database-driven system for defining and applying compliance rules, managed via the admin UI and AI-proposable.
-   **Web Intelligence:** Integrates real-time web search (`Serper.dev API`) for methodology status verification and knowledge refreshing.
-   **Document Synchronization:** Automated downloading and ingestion of methodologies, program standards, guides, and project documents from public catalogs (Verra VCS, CDM/UNFCCC, Gold Standard).
-   **Carbon Project Intelligence:** A dashboard providing analytics on carbon projects from Verra VCS and Gold Standard registries.
-   **Methodology Database:** A structured database of 192+ carbon methodologies used for selection, AI context injection, and deprecation warnings.
-   **Project Workspace (My Projects):** User-facing project management with document upload, AI-powered review (with PDD-MR cross-referencing), and AI writing assistant.
-   **AI Writing - Full Document Generation:** The Write/Draft tab supports both per-section and full document generation, displaying a template view with progress tracking.
-   **AI Writing - Template View:** The Write/Draft tab displays the document as a structured template with section details, generated content, and requirements.
-   **AI Writing - Template Compliance:** All 7 guide files include `content_format`, `format_instructions`, and (for structured sections) `template_scaffold` fields per section. The `template_scaffold` contains the exact table/block structure extracted from the official GS/VCS Word templates (`.docx`), so the AI fills in the actual template rather than inventing a similar format. Format types: prose, table, parameter_blocks, checklist, equations_and_prose, summary_table. Template scaffolds cover: project boundary tables, parameter blocks (ex ante + monitored), SDG summary tables, year-by-year estimates, contact info, audit history, safeguarding checklists, gender assessment, and grievance mechanisms.
-   **Search & AI Retrieval:** Implements a hybrid search mechanism combining semantic search (pgvector) and keyword search (PostgreSQL `tsvector`).
-   **Methodology Knowledge Base:** A multi-layered, format-resilient system for extracting and storing methodology intelligence, replacing one-shot AI parsing with a structured pipeline for programmatic and AI-driven structure detection, multi-pass extraction, and verification. Stores methodologies as semantically tagged chunks (`applicability`, `equations`, `parameters`, etc.) in `methodology_knowledge` and `methodology_structure` tables.
-   **Methodology Calculation Engine:** An AI-powered system for analyzing methodologies and calculating emission reductions. Methodologies are parsed once and cached in `methodology_parsed` table. Project settings and intake data drive default parameter resolution. The `calculation_engine.py` runs calculations.
-   **Document Exporter:** Exports calculation results to Excel and generates filled Word templates. All 7 doc types now have official `.docx` templates mapped in `TEMPLATE_FILES`: GS PDD v1.5, GS MR v1.1 (PerfCert), GS VPA-DD v2.3, GS PoA-DD v2.2, VCS PD v4.4, VCS MR v4.4, VCS ValVer v4.4. GS PDD and MR use `Heading 5` style with `A.1`-style section IDs and `>>` placeholders; `_fill_gs_template()` handles both via `GS_PDD_SUBSECTION_ALIASES` and `GS_MR_SUBSECTION_ALIASES` + `GS_MR_TEMPLATE_REMAP` (the MR template numbers sections differently: template A.3 → guide A.4). GS VPA-DD and PoA-DD use `Section List`/`Section List 2nd`/`Section Title` styles with title-based matching via `_fill_gs_titled_template()` and `GS_VPA_DD_TITLE_MAP`/`GS_POA_DD_TITLE_MAP`. VCS templates use `Heading` + `Instruction` styles via `_fill_vcs_template()`. Falls back to generic Word generation only if template loading fails. Key features: (1) uses template's own font (Verdana 11pt for GS) for inserted text, (2) strips AI-generated duplicate section titles, (3) fills KPI table fields and ticks checkboxes from project intake data, (4) renders markdown tables as proper Word tables with borders.

## External Dependencies

-   **PostgreSQL:** Primary database for all application data.
-   **pgvector:** PostgreSQL extension for semantic search.
-   **OpenAI API:** For AI review (`gpt-4o-mini`), embeddings (`text-embedding-3-small`), and AI-driven document attribute detection.
-   **Serper.dev API:** For real-time web searches.
-   **Verra APIs:** WordPress REST API (methodology PDFs), Verra JSON API (project documents and metadata).
-   **Gold Standard Public API:** For project metadata and document templates.
-   **UNFCCC (CDM) resources:** For CDM methodology booklets and tools.
-   **Python Libraries:** `FastAPI`, `Streamlit`, `Uvicorn`, `psycopg2-binary`, `pdfplumber`, `tiktoken`, `python-docx`, `openpyxl`, `PyYAML`, `rapidfuzz`, `pytest`.