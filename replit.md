# CarbonGPT — MVP

## Overview

CarbonGPT is a modular compliance analysis tool designed to streamline and automate carbon credit project development and verification. It provides a comprehensive platform for managing, analyzing, and ensuring compliance of carbon projects against various international standards such as Gold Standard and Verra VCS. The project aims to reduce the manual effort involved in navigating complex regulatory frameworks, minimize errors, and accelerate the validation and verification process. By leveraging AI, web intelligence, and a robust document repository, CarbonGPT enhances efficiency, accuracy, and transparency in the carbon market, ultimately contributing to faster climate action and improved project quality.

## User Preferences

I want iterative development. Ask before making major changes. I prefer detailed explanations. Do not make changes to the folder `carbongpt/tests/`. Do not make changes to the file `carbongpt/ui/admin_app.py`.

## System Architecture

CarbonGPT is built with Python 3.11, FastAPI for backend services, and Streamlit for the user interface.

**UI/UX Decisions:**
The application features two primary interfaces:
- **Compliance Analyzer + Document Repository + Carbon Intelligence (Streamlit UI):** This is the main user-facing application for document analysis, repository management, and carbon project analytics.
- **Admin App (Streamlit - separate port):** A standalone interface for administrative tasks, though primarily managed through the main UI's admin sections.

**Technical Implementations:**

-   **Document Processing:** Utilizes `pdfplumber` for PDF parsing and `python-docx` for DOCX files. Documents undergo section extraction, AI-driven auto-detection of standards and categories, chunking (`tiktoken`), and embedding (`OpenAI text-embedding-3-small`).
-   **AI Review System (beta):** An asynchronous process (`ai_review_worker.py`) for in-depth AI-powered document review using `gpt-4o-mini`. It supports knowledge-augmented review (RAG) by retrieving relevant context from the document repository.
-   **Compliance Rules Engine:** A database-driven system for defining and applying compliance rules (e.g., methodology status, crediting period, eligibility). Rules are managed via the admin UI and can be AI-proposed.
-   **Web Intelligence:** Integrates real-time web search (`Serper.dev API`) to verify methodology statuses, refresh knowledge, and propose new compliance rules.
-   **Document Synchronization:** Automated downloading and ingestion of methodologies, program standards, guides, and project documents from public catalogs (Verra VCS, CDM/UNFCCC, Gold Standard).
-   **Carbon Project Intelligence:** A dashboard providing analytics on carbon projects sourced directly from Verra VCS and Gold Standard registries, including project overview, country-specific details, and methodology analysis.
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
-   **Python Libraries:** `FastAPI`, `Streamlit`, `Uvicorn`, `psycopg2-binary`, `pdfplumber`, `tiktoken`, `python-docx`, `PyYAML`, `rapidfuzz`, `pytest`.