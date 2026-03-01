# CarbonGPT — MVP

## Overview

CarbonGPT is a modular compliance analysis tool designed to streamline and automate carbon credit project development and verification. It provides a comprehensive platform for managing, analyzing, and ensuring compliance of carbon projects against various international standards such as Gold Standard and Verra VCS. The project aims to reduce the manual effort involved in navigating complex regulatory frameworks, minimize errors, and accelerate the validation and verification process. By leveraging AI, web intelligence, and a robust document repository, CarbonGPT enhances efficiency, accuracy, and transparency in the carbon market, ultimately contributing to faster climate action and improved project quality.

## User Preferences

I want iterative development. Ask before making major changes. I prefer detailed explanations. Do not make changes to the folder `carbongpt/tests/`. Do not make changes to the file `carbongpt/ui/admin_app.py`.

## System Architecture

CarbonGPT is built with Python 3.11, FastAPI for backend services, and Streamlit for the user interface.

**UI/UX Decisions:**
The application features a streamlined two-section navigation:
- **Workspace (Streamlit UI - main page):** Contains two tabs: "My Projects" (project workspace with documents, AI review, AI writing assistant) and "Carbon Intelligence" (dashboard with 8,900+ projects from Verra and Gold Standard registries). Premium CSS styling with dark sidebar, Inter font, gradient branding, and polished metric cards.
- **Admin (Streamlit UI - second page):** Document repository management, compliance rules, knowledge base, methodology sync, and web intelligence tools.
- **Admin App (Streamlit - separate port):** A standalone admin interface (legacy).
- The standalone Compliance Analyzer was removed (its functionality is fully covered by the Review tab inside each project workspace, which provides better context-aware review with PDD-MR cross-referencing).

**Technical Implementations:**

-   **Document Processing:** Utilizes `pdfplumber` for PDF parsing and `python-docx` for DOCX files. Documents undergo section extraction, AI-driven auto-detection of standards and categories, chunking (`tiktoken`), and embedding (`OpenAI text-embedding-3-small`).
-   **AI Review System (beta):** An asynchronous process (`ai_review_worker.py`) for in-depth AI-powered document review using `gpt-4o-mini`. It supports knowledge-augmented review (RAG) by retrieving relevant context from the document repository.
-   **Compliance Rules Engine:** A database-driven system for defining and applying compliance rules (e.g., methodology status, crediting period, eligibility). Rules are managed via the admin UI and can be AI-proposed.
-   **Web Intelligence:** Integrates real-time web search (`Serper.dev API`) to verify methodology statuses, refresh knowledge, and propose new compliance rules.
-   **Document Synchronization:** Automated downloading and ingestion of methodologies, program standards, guides, and project documents from public catalogs (Verra VCS, CDM/UNFCCC, Gold Standard).
-   **Carbon Project Intelligence:** A dashboard providing analytics on carbon projects sourced directly from Verra VCS and Gold Standard registries, including project overview, country-specific details, and methodology analysis.
-   **Methodology Database:** A structured database of 192+ carbon methodologies (ACM, AM, AMS, VM, VMR, GS families) extracted from real registry data. Each methodology stores code, name, standard, category, sector, status (active/deprecated), applicability conditions, and project count. Used for: (1) searchable methodology picker in project creation/settings, (2) AI context injection for smarter drafting and review, (3) deprecation warnings and superseded-by tracking. Table: `methodologies`. Population: `carbongpt/repository/methodology_db.py`. API: `/projects/methodologies`, `/projects/methodologies/{code}`, `/projects/methodologies/categories`.
-   **Project Workspace (My Projects):** User-facing project management with document upload, AI-powered review (with PDD-MR cross-referencing), and AI writing assistant for drafting PDD/MR sections. Supports reference document uploads for context-aware AI assistance. The methodology selector uses the methodology database for accurate selection. Database tables: `user_projects`, `project_documents`, `project_write_sessions`. API routes in `carbongpt/app/project_routes.py`. AI engine in `carbongpt/core/ai_writer.py`.
-   **Search & AI Retrieval:** Implements a hybrid search mechanism combining semantic search (pgvector cosine distance) and keyword search (PostgreSQL `tsvector`) for efficient content retrieval.

**Feature Specifications:**

-   **Analysis Endpoints:** Provide functionality for uploading documents, analyzing them against YAML rules or templates, and initiating/monitoring asynchronous AI reviews.
-   **Admin/Document Repository Endpoints:** Enable CRUD operations for standards, documents, compliance rules, and facilitate semantic search across embedded content. Includes features for re-ingestion, repository statistics, and web intelligence tasks.
-   **Document Categories:** Supports a wide range of document types including `standard_text`, `methodology`, `guidance`, `template`, and various `example` documents.
-   **Template Registry:** Manages internal document templates defined in `registry.yaml` for specific standards and document types.

## External Dependencies

-   **PostgreSQL:** Primary database for storing all application data, including document metadata, sections, chunks, compliance rules, carbon project data, and configurations.
-   **pgvector:** PostgreSQL extension used for efficient semantic search by storing and querying vector embeddings.
-   **OpenAI API:** Utilized for AI review (`gpt-4o-mini`), generating text embeddings (`text-embedding-3-small`), AI-driven auto-detection of document attributes, and generating document summaries.
-   **Serper.dev API:** Integrated for performing real-time web searches as part of the Web Intelligence features.
-   **Verra APIs:**
    -   WordPress REST API: For downloading Verra methodology PDFs.
    -   Verra JSON API: For discovering and retrieving project documents and metadata from the Verra registry.
-   **Gold Standard Public API:** For retrieving project metadata and document templates.
-   **UNFCCC (CDM) resources:** For downloading CDM methodology booklets and tools.
-   **Python Libraries:** `FastAPI`, `Streamlit`, `Uvicorn`, `psycopg2-binary`, `pdfplumber`, `tiktoken`, `python-docx`, `openpyxl`, `PyYAML`, `rapidfuzz`, `pytest`.

## Methodology Calculation Engine

The platform includes an AI-powered methodology analysis and emission reduction calculation system:

-   **Methodology Parser (`carbongpt/core/methodology_parser.py`):** Uses GPT-4o to extract calculation frameworks from methodology documents. Now extracts structured data including: parameter `category` (methodology_default, monitored, calculated, project_input, qualitative), `equation_role` (input, intermediate, output, none), `defaults_by_context` (numeric defaults keyed by fuel type/GWP version), and `context_dimensions` (choices that affect defaults, e.g. baseline_fuel: wood/charcoal, gwp_version: AR4/AR5). Works generically across any methodology.
-   **Pre-parsed Methodology Cache (`methodology_parsed` table):** Methodologies are parsed once and stored in the database. Loads instantly from DB — no AI call needed. Admin endpoints: `POST /admin/methodology-parsed/parse`, `POST /admin/methodology-parsed/batch`.
-   **Project Settings:** `user_projects` table includes `crediting_period_start` (DATE), `crediting_period_years` (INTEGER, default 7), `project_settings` (JSONB — stores context dimension selections like baseline_fuel, gwp_version). These drive default resolution in the Calculations tab.
-   **Calculations Tab:** Parameters grouped by category: Methodology Defaults (pre-filled from context), Monitored/Field Data, Calculated (disabled). Units shown in brackets. Defaults auto-resolve based on project settings (e.g. wood+AR5 → NCV=0.0156, EF_CO2=112, EF_nonCO2=9.46). Crediting period from project settings.
-   **Calculation Engine (`carbongpt/core/calculation_engine.py`):** Takes parsed methodology output + user-provided project-specific inputs and runs emission reduction calculations for each year of the crediting period.
-   **Document Exporter (`carbongpt/core/doc_exporter.py`):** Exports calculation results to Excel and generates filled Word templates.
-   **API Endpoints:** `GET /projects/{id}/methodology-data`, `POST /projects/{id}/parse-methodology`, `POST /projects/{id}/calculate`, `POST /projects/{id}/export-calculation`, `POST /projects/{id}/generate-template`
-   **UI Tabs:** "Calculations" tab (auto-loads parsed methodology, grouped param inputs with defaults, run calcs), "Settings" tab (crediting period, context dimensions), "Export" tab (Word/Excel).