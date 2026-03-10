# CarbonGPT — Technical Overview

## Overview

CarbonGPT is an AI-powered operating system for carbon credit projects. It facilitates the entire lifecycle of carbon projects, from development and verification to management. The platform generates project documents (PDDs, MRs, PoA-DDs, VPA-DDs, ValVer) compliant with Gold Standard (GS4GG) and Verra VCS. Key capabilities include AI-assisted drafting, automated compliance checks, intelligence extraction, a findings response assistant, emission reduction scenario simulation, carbon finance modeling, project lifecycle management, monitoring, audit simulation, evidence tracking, portfolio analytics, and a context-aware ChatAI. CarbonGPT aims to streamline carbon project development, enhance accuracy, and accelerate time to market.

## User Preferences

- Iterative development; ask before making major changes
- Detailed explanations preferred
- DO NOT modify: `carbongpt/tests/` or `carbongpt/ui/admin_app.py`
- No emoji in UI — text labels only
- No hardcoding: improvements through AI prompts and guide files only

## System Architecture

CarbonGPT uses a Python-based backend with FastAPI and a Streamlit frontend. It integrates with a PostgreSQL database, utilizing the pgvector extension for vector search and raw SQL for database interactions.

**Frontend:**
A single Streamlit application (`streamlit_app.py`) serves as the UI, featuring modular components and `st.session_state` for state management. Navigation includes Workspace, Portfolio, and Admin pages. The Project workspace is organized into 11 tabs: Setup, Documents, Parameters, ER Simulator, Write/Draft, Review, Audit, Findings, Lifecycle, Monitoring, and Export. A central AI Copilot chat widget enables natural language interaction for project management.

**UI Design System:**
The UI emphasizes a premium SaaS feel with the Inter font and a teal/green color gradient. It includes consistent design elements such as 4-column metric cards, project headers with badges and quick actions, SVG icons for section headers, an activity feed, and a "Next Steps" panel. The system provides cross-tab readiness banners, post-action suggestions, lifecycle-aware tab highlighting, and AI Copilot action cards. Methodology recommendations, color-coded status indicators, and native Streamlit components are used throughout. Parameter deduplication and quick action buttons enhance user efficiency.

**AI Copilot System:**
The `carbongpt/core/copilot.py` module orchestrates AI interactions using OpenAI's function calling for intent detection. It supports actions like project creation, parameter initialization, ER simulation, drafting, auditing, reviewing, methodology suggestion, status checks, and navigation. A methodology recommendation engine maps keywords to relevant technologies.

**Backend:**
The FastAPI backend organizes routes into project-specific and admin modules. It manages project CRUD operations, document handling, AI-driven intelligence extraction, drafting, review processes, findings responses, document export, parameter management, emission reduction calculations, lifecycle management, monitoring, issuance tracking, evidence management, and audit simulations.

**AI & NLP:**
CarbonGPT leverages OpenAI's GPT models (gpt-4o, gpt-4o-mini) for language inference and `text-embedding-3-small` for embeddings. Key AI features include adaptive model selection, project-level RAG with hybrid vector+keyword search, cross-section consistency validation, output validation against `must_include` items, and an 8-layer Research Orchestrator. A `TOOL33 Defaults Module` (`tool_defaults.py`) provides structured defaults from various climate methodologies and guidelines.

**Core Engine Modules:**
- **Methodology Rules:** (`carbongpt/core/methodology_rules.py`) Centralizes methodology-derived field definitions (activity_type, sectoral_scope, scale_options, fuel_field_mode) and standard-specific defaults (crediting period: GS=5yr, Verra=7yr). Used by the Setup UI to auto-derive fields and avoid duplicate inputs.
- **Parameter Engine:** (`carbongpt/core/parameter_engine.py`) Manages parameters with validation, source tracking, dependency tracking, and auto-initialization from methodology defaults. Includes canonical fuel normalization, parameter status tracking, and derived parameter computation (num_households from num_devices/devices_per_household, num_beneficiaries from num_households*household_size). Derived values auto-recompute when dependent inputs change. CF parameter hidden when neither fuel is charcoal. method_selection auto-derived from fuel choices (same fuel=Method 1, different=Method 2).
- **ER Simulator:** (`carbongpt/core/er_simulator.py`) Performs deterministic emission reduction calculations for various methodologies, supporting year-by-year projections, scenario management, sensitivity analysis, and carbon finance modeling. Features a cohort-based deployment engine with configurable ramp-up, timing, technology lifetime, drop-off, and usage rate models.
- **Lifecycle Manager:** (`carbongpt/core/lifecycle_manager.py`) Oversees project lifecycle stages, task management, monitoring initialization, and issuance tracking.
- **Evidence Engine:** (`carbongpt/core/evidence_engine.py`) A methodology-agnostic engine for extracting and linking claims/parameters to source documents. It includes dynamic parameter selection, evidence decision-making, and robust extraction quality features like anti-hallucination prompts and quote validation.
- **Audit Simulator:** (`carbongpt/core/audit_simulator.py`) Simulates VVB audits, performing parameter validation, evidence gap analysis, section consistency checks, and compliance verification with risk scoring.
- **Project State Engine:** (`carbongpt/core/project_state.py`) Provides comprehensive project health assessments, including readiness scores, stage evaluation, and detailed breakdowns of project components.

**Database Schema:**
The database includes tables for standards, documents, compliance rules, carbon projects, user projects, and methodology intelligence. New tables for the Carbon Operating System include `project_parameters`, `project_lifecycle`, `project_tasks`, `evidence_links`, `er_scenarios`, `er_scenario_years`, `issuance_records`, `monitoring_tasks`, and `audit_simulation_results`. These tables support centralized parameter storage, lifecycle management, evidence linking, scenario management, and audit reporting.

## External Dependencies

-   **PostgreSQL:** Primary relational database.
-   **pgvector:** PostgreSQL extension for vector similarity search.
-   **OpenAI API:** For LLM inference (GPT-4o, GPT-4o-mini) and embeddings (text-embedding-3-small).
-   **Serper.dev API:** Used for web search to verify methodology status.
-   **Verra REST API:** Accesses registry project metadata and methodology PDFs.
-   **Gold Standard API:** Retrieves project data and document templates.
-   **UNFCCC/CDM resources:** Provides CDM methodology booklets and tools.