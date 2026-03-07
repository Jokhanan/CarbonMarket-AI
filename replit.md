# CarbonGPT — Technical Overview

## Overview

CarbonGPT is an AI-powered carbon project operating system designed for end-to-end carbon credit project development, verification, and management. It streamlines the creation, review, and export of crucial project documents (PDDs, MRs, PoA-DDs, VPA-DDs, ValVer) compliant with Gold Standard (GS4GG) and Verra VCS standards. The platform offers AI-assisted drafting, automated compliance review, intelligence extraction, a findings response assistant, document export, parameter intelligence, emission reduction scenario simulation, carbon finance modeling, project lifecycle management, monitoring management, audit simulation, evidence tracking, portfolio analytics, and a project-context-aware ChatAI assistant.

## User Preferences

- Iterative development; ask before making major changes
- Detailed explanations preferred
- DO NOT modify: `carbongpt/tests/` or `carbongpt/ui/admin_app.py`
- No emoji in UI — text labels only
- No hardcoding: improvements through AI prompts and guide files only

## System Architecture

The CarbonGPT platform utilizes a Python-based backend with FastAPI and a Streamlit frontend. It employs a PostgreSQL database with the pgvector extension for vector search, and raw SQL for database interactions (no ORM).

**Frontend:**
The UI is a single Streamlit application (`streamlit_app.py`) with modular UI components in separate files. Navigation includes Workspace, Portfolio, and Admin pages. Project workspace has 11 tabs: Setup, Documents, Parameters, ER Simulator, Write/Draft, Review, Audit, Findings, Lifecycle, Monitoring, Export. Uses `st.session_state` for state management and custom CSS with teal brand color (`#0d9488`). An AI Copilot chat widget serves as the central interface for project management through natural language.

**UI Design System:**
- Premium SaaS-level interface with Inter font, teal/green brand gradient
- Overview metric cards (4-column grid) on both workspace home and project workspace pages
- Project header with type/standard/status badges, methodology/country with icons, and quick action buttons
- Section header icons for all 11 workspace tabs (SVG icons with colored backgrounds)
- Activity feed in project workspace (collapsible expander)
- Smart "Next Steps" panel on project overview (analyzes param/doc/draft/sim/audit state, shows 2-3 prioritized next actions)
- Cross-tab readiness banners (ER Simulator, Review, Write/Draft, Audit tabs show prerequisite status with ready/warning/info styling)
- Post-action suggestions after key operations (ER simulation results, audit results)
- Lifecycle-aware tab highlighting with "(Next)" suffix on the recommended next tab
- AI Copilot chat widget with action cards, navigation buttons, and suggestion chips
- Methodology recommendation panel in Setup tab based on project description
- Color-coded status indicators (green=complete, amber=missing, red=error)
- Card-based layout with subtle shadows, rounded corners, hover interactions
- CSS variables for consistent theming (surfaces, borders, shadows, radii, transitions)

**UI Modules:**
- `carbongpt/ui/parameter_ui.py` — Parameter Intelligence Dashboard
- `carbongpt/ui/er_simulator_ui.py` — ER Scenario Simulator with finance
- `carbongpt/ui/lifecycle_ui.py` — Lifecycle management, monitoring, issuance tracking
- `carbongpt/ui/portfolio_ui.py` — Portfolio analytics dashboard
- `carbongpt/ui/audit_ui.py` — Audit simulation interface

**AI Copilot System:**
- `carbongpt/core/copilot.py` — Unified AI orchestrator with OpenAI function calling
- Uses OpenAI tool_choice for intent detection from natural language
- Available actions: create_project, initialize_parameters, run_er_simulation, draft_section, run_audit, run_review, suggest_methodology, get_project_status, navigate_to_tab
- Methodology recommendation engine with keyword-to-technology mapping for cookstoves, solar, wind, biogas, waste, forestry, transport, agriculture, charcoal, rice
- Integrated into `/projects/chat` endpoint — replaces simple GPT chat with copilot orchestration
- Chat widget shows action cards (styled results), navigation buttons, and suggestion chips

**Backend:**
The FastAPI application organizes routes into project-specific and admin modules. It handles project CRUD, document uploads, AI intelligence extraction, drafting, review, findings response, document export, parameter management, ER calculations, lifecycle management, monitoring tasks, issuance tracking, evidence management, and audit simulation.

**AI & NLP:**
The core AI components leverage OpenAI's GPT models for language model inference and `text-embedding-3-small` for embeddings. Key AI architecture features:
- **Adaptive model selection**: Complex sections use gpt-4o; simple narrative sections use gpt-4o-mini
- **Project-level RAG**: Uploaded documents are chunked, embedded, stored in `project_doc_chunks` with hybrid vector+keyword search
- **Cross-section consistency validation**: Validates all sections together for contradictions
- **Output validation**: Checks against guide's `must_include` items with coverage scores
- **Multi-layer Research Orchestrator**: 8 research layers with source priorities and confirm/reject workflow
- **TOOL33 Defaults Module**: `tool_defaults.py` provides structured defaults from CDM TOOL33 v03.0, IPCC 2006, VM0050, TPDDTEC, ACM0002, AMS-I.D. Key functions: `get_fnrb_for_country()`, `get_fuel_defaults()`, `get_defaults_for_methodology()`

**Core Engine Modules:**
- `carbongpt/core/parameter_engine.py` — Centralized parameter management with validation, source tracking, dependency tracking, and auto-initialization from methodology defaults
- `carbongpt/core/er_simulator.py` — Deterministic emission reduction calculations for cookstove (VM0050/TPDDTEC) and grid (ACM0002/AMS-I.D.) methodologies, year-by-year projections, scenario management, sensitivity analysis, carbon finance modeling
- `carbongpt/core/lifecycle_manager.py` — Project lifecycle stages (Feasibility through Issuance), task management, monitoring task initialization, issuance tracking, portfolio analytics
- `carbongpt/core/evidence_engine.py` — Evidence linking (parameters/sections to source documents), evidence completeness scoring, citation generation
- `carbongpt/core/audit_simulator.py` — Simulated VVB audit with parameter validation, evidence gap analysis, section consistency checks, compliance verification, risk scoring

## Database Schema

### Original Tables
- `standards`, `standard_versions` — Standard definitions (Verra, Gold Standard)
- `documents`, `document_sections`, `document_chunks` — Global document repository with embeddings
- `document_references` — Cross-document references
- `compliance_rules` — YAML-based compliance rules
- `carbon_projects` — Synced registry projects
- `user_projects` — User project data with intake forms
- `project_documents` — Uploaded project files
- `project_doc_chunks` — Project document embeddings for RAG
- `project_write_sessions` — AI-generated and user-edited drafts
- `methodologies`, `methodology_parsed`, `methodology_knowledge`, `methodology_structure` — Methodology intelligence
- `findings_knowledge` — VVB findings patterns
- `research_results`, `research_source_priority` — Research orchestrator data

### Carbon Operating System Tables (New)
- `project_parameters` — Centralized parameter store (value, source, validation, evidence, min/max, uncertainty, ex-ante/ex-post, dependencies)
- `project_lifecycle` — Stage transitions with timestamps
- `project_tasks` — Tasks per lifecycle stage with priorities and deadlines
- `evidence_links` — Links claims/parameters to source documents/chunks
- `er_scenarios` — Saved emission reduction scenarios with parameter overrides
- `er_scenario_years` — Year-by-year calculation results
- `issuance_records` — Issued credits, vintages, verification cycles
- `monitoring_tasks` — Scheduled monitoring activities from methodology requirements
- `audit_simulation_results` — Saved audit simulation reports with findings

## Key Files

- `carbongpt/ui/streamlit_app.py` — Main Streamlit UI (6400+ lines)
- `carbongpt/ui/admin_app.py` — Admin dashboard (DO NOT MODIFY)
- `carbongpt/core/ai_writer.py` — AI drafting engine
- `carbongpt/core/tool_defaults.py` — TOOL33 and methodology defaults
- `carbongpt/core/parameter_engine.py` — Parameter intelligence engine
- `carbongpt/core/er_simulator.py` — ER scenario simulator
- `carbongpt/core/lifecycle_manager.py` — Lifecycle and monitoring management
- `carbongpt/core/evidence_engine.py` — Evidence and citation engine
- `carbongpt/core/audit_simulator.py` — Audit simulation engine
- `carbongpt/core/research_orchestrator.py` — Multi-layer research
- `carbongpt/app/project_routes.py` — API routes
- `carbongpt/repository/schema.py` — Database schema

## External Dependencies

- **PostgreSQL:** Primary relational database
- **pgvector:** PostgreSQL extension for vector similarity search
- **OpenAI API:** LLM inference (GPT-4o, GPT-4o-mini) and embeddings (text-embedding-3-small)
- **Serper.dev API:** Web search for methodology status verification
- **Verra REST API:** Registry project metadata and methodology PDFs
- **Gold Standard API:** Project data and document templates
- **UNFCCC/CDM resources:** CDM methodology booklets and tools

## App Configuration

- Streamlit on port 5000, FastAPI on port 3000
- Model config: `CARBONGPT_AI_MODEL` (default gpt-4o-mini), `CARBONGPT_UPGRADE_MODEL` (default gpt-4o)
- TOOL33 fNRB: `TOOL33_FNRB_BY_COUNTRY` is `{"Country": float}` (simple fractions)
- Charcoal EFs: Wood EF_nonCO2=9.46; Charcoal combustion=5.865, with_production=44.83, cap=92.29 (AR5 GWP)
- `get_fuel_defaults(fuel, include_production_emissions=False)` handles charcoal scenarios
