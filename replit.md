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
- **Project Brain:** (`carbongpt/core/project_brain.py`) Full orchestration layer with: **7-stage derived project model** (setup→parameterization→simulation→drafting→review→audit_prep→submission_ready), **5-phase pipeline** (Define/Quantify/Draft/Validate/Submit), **methodology-aware required parameter blockers** per methodology code (VM0050/TPDDTEC/ACM0002/AMS-I.D./GS-MECD), **cross-module synthesis** (scenario_param_drift, audit_rerun_needed, evidence_coverage_rate, draft_coverage_rate, audit_car_params), **13-signal automation opportunities** with priority ranking, **stage-gated next-best-action** with per-stage fallback defaults, **parameter outlier detection** against methodology benchmark ranges, and **tab badge computation** (maps tab index → {count, severity} for blocker/warning/caution). All outputs cached in `st.session_state[f"brain_state_{project_id}"]` for the workspace session.

**Wizard (Project Creation Flow):**
The New Project wizard in `_render_new_project_wizard` (streamlit_app.py) is project-first, not document-first. Step 1 presents 3 paths:
- **New project** → shows only Standalone PDD and PoA-DD cards → existing step 2/3 methodology wizard
- **Add to existing project** → parent project picker → doc type selection (MR, VPA-DD, ValVer) → step 2 pre-filled with parent's standard/country
- **Import existing document** → file upload (PDF/DOCX) → AI extracts project name/standard/methodology/country → pre-fills step 2
The "Import Document" button also appears on the home screen alongside "New Project". The import endpoint is `POST /api/projects/import-document`.

**Monitoring Periods:**
The `monitoring_periods` DB table (id, project_id, period_number, period_start, period_end, status, notes, mr_project_id) tracks discrete monitoring cycles as first-class records. The Monitoring tab in the project workspace shows these periods first, with an "Add Period" form and a "Generate MR" button per period that auto-creates a linked monitoring_report child project. Store functions: `create/list/update/delete_monitoring_period`. API routes: `GET/POST /projects/{id}/monitoring-periods`, `PATCH/DELETE /projects/{id}/monitoring-periods/{pid}`.

**Database Schema:**
The database includes tables for standards, documents, compliance rules, carbon projects, user projects, and methodology intelligence. New tables for the Carbon Operating System include `project_parameters`, `project_lifecycle`, `project_tasks`, `evidence_links`, `er_scenarios`, `er_scenario_years`, `issuance_records`, `monitoring_tasks`, `audit_simulation_results`, and `monitoring_periods`. These tables support centralized parameter storage, lifecycle management, evidence linking, scenario management, audit reporting, and monitoring period tracking.

## Methodology Pack Manager

The Methodology Pack Manager provides a curated knowledge infrastructure for grounding CarbonGPT AI responses in real approved-project precedent.

**Schema tables** (`carbongpt/repository/schema.py`):
- `methodology_packs` — one pack per methodology code + registry, with readiness score and 5 hard gates
- `methodology_pack_document_links` — links existing repository documents to packs with role, confidence flags, and provenance
- `pack_findings` — DOE findings (CAR/CL/FAR) extracted from val/ver reports, linked to source documents
- `methodology_pack_candidates` — Carbon Intelligence project candidates for a pack

**Core modules**:
- `carbongpt/repository/pack_store.py` — CRUD for packs, document links, readiness evaluation (G1–G5 hard gates + qualitative score)
- `carbongpt/repository/pack_classifier.py` — Repository audit: detects methodology codes from document text, classifies doc types, auto-builds packs from scan results
- `carbongpt/repository/pack_builder.py` — **AI-Assisted Auto Pack Builder**: orchestrates full methodology intelligence workflow

**AI-Assisted Auto Pack Builder** (`pack_builder.py`):
1. **Methodology Requirements Analyzer** — static knowledge base for TPDDTEC, VM0050, VM0042, ACM0002, AMS-I.D, AMS-I.E plus dynamic analysis from ref_methodologies and repository chunks. Returns a `MethodologyProfile` with required docs, tool references, and confidence levels (confirmed / probable / unknown).
2. **Repository-First Discovery** — scans all document chunks for methodology codes; classifies docs into high (≥75%), medium (55–75%), low (<55%) confidence tiers; auto-links high-confidence docs into the pack.
3. **Carbon Intelligence Candidate Discovery** — queries `carbon_projects` + `project_methodology_codes` for matching projects; ranks by registration status, geographic diversity, estimated credits, and existing repo coverage. Also searches the freeform `methodology` field (needed for TPDDTEC which isn't in pmc).
4. **Remote Document Discovery** — attempts to download PDFs from the Verra Registry API for Verra projects; gracefully fails for Gold Standard (Cloudflare-blocked); logs all attempts to the missing-items report.
5. **Findings Extraction** — scans validation/verification report chunks with regex for CAR/CL/FAR/CR patterns; inserts new findings into `pack_findings` table.
6. **Missing-Items Report Generator** — compares methodology profile requirements against what's in the pack; generates prioritised list of critical / recommended / optional items with specific admin action steps.

**API endpoints** (`carbongpt/app/pack_routes.py`):
- `GET  /admin/packs/analyze-requirements/{code}` — methodology requirements profile
- `GET  /admin/packs/discover-candidates/{code}` — CI project candidate ranking
- `POST /admin/packs/ai-build` — full AI-assisted pack build (supports dry_run, max_remote_attempts, extract_findings)
- `POST /admin/packs/audit` — full repository audit with methodology detection
- `POST /admin/packs/auto-build` — lightweight pack build (classifier only, no CI/remote discovery)
- `POST /admin/packs/auto-build-all` — auto-build all detected methodologies

**Streamlit Admin UI** — "Methodology Packs" tab has 5 sub-tabs:
1. Overview & Readiness — score gauge + hard gate status + activate/archive buttons
2. Candidate Projects — Carbon Intelligence candidates with country/status filters
3. Documents — upload + link + manage documents per pack
4. Findings — CAR/CL/FAR findings manager
5. **Auto-Build** — Run AI-Assisted Build / Dry Run / Discover CI Candidates / Extract Findings buttons; Requirements Profile expander; full build report with Found/Suggested/Remote Discovery/Missing Items sections

**Readiness model**:
- G1: methodology document ingested (500+ words)
- G2: PDD count ≥ floor(target/2)
- G3: extraction quality ≤ 30% poor PDFs
- G4: ≥ 60% linked projects are registered
- G5: at least one Monitoring Report ingested
- Score 0–100 (gates + qualitative bonuses for diversity, findings, tool docs)
- Status `ready_for_indexing` requires score ≥ 60 AND all 5 gates passing

**AI fallback**: `_get_methodology_context()` in `ai_writer.py` uses pack-first retrieval when a pack is indexed, falls back to legacy `methodology_library` metadata transparently. No regression possible.

## Deep Implementation Audit Findings & Fixes (2026-03)

### Bugs Fixed

**1. `run_scenario` never passed `method_id` to cookstove calculators** (`carbongpt/core/er_simulator.py`)
- Root cause: DB query only read `methodology, crediting_period_years, crediting_period_start`; `methodology_settings` was never fetched.
- Impact: For TPDDTEC projects, Method 2 (locked defaults) and Method 3 (fuel-switch, no fNRB on PE) were silently ignored. All TPDDTEC scenarios ran as Method 1 regardless of what was set in the wizard.
- Fix: Extended DB query to also `SELECT methodology_settings`; parses `calculation_method` or `method_id` from the JSON blob; passes `method_id=method_id` to both `calculate_cookstove_er` and `calculate_cookstove_er_cohort`.

**2. TPDDTEC ER simulator override used wrong key and wrong unit label** (`carbongpt/ui/er_simulator_ui.py`)
- Root cause: Override stored `overrides["SFC_baseline"]` (with label "kg/person/yr"), but the calculator reads `params["baseline_fuel_consumption"]` (in t/device/yr). SFC_baseline is kg/device/day; baseline_fuel_consumption = SFC_baseline × 365 / 1000.
- Impact: Any TPDDTEC scenario override for fuel consumption was silently discarded; the stored parameter value was used instead, making the override non-functional.
- Fix: Override now sets both `SFC_baseline` (raw measurement) AND computes `baseline_fuel_consumption = sfc_b × 365 / 1000` (what the calculator reads). Unit label corrected to "kg/device/day". Display value is back-derived from `baseline_fuel_consumption` if available. Same fix applied to SFC_project → project_fuel_consumption.

**3. MECD `run_scenario` output had no standard envelope** (`carbongpt/core/er_simulator.py`)
- Root cause: `calculate_mecd_er` returns `{yearly, total_er_tCO2e, avg_annual_er_tCO2e, …}`; `save_scenario` expects `result["summary"]` and `result["years"]`; `_render_er_results` expects `result["summary"]` with specific keys.
- Impact: Calling `save_scenario` on any GS-MECD project would crash with `KeyError: 'summary'`.
- Fix: Added `_normalize_mecd_result()` which wraps the raw MECD output into the standard envelope: `summary{total_er, average_annual_er, crediting_years, deployment_mode}`, `years` list with `year_number/calendar_year/baseline_emissions/…`, `year_by_year` (alias for charts), and `calculation_steps` for the Excel workbook.

### Known Open Items
- **MECD ER Simulator UI**: GS-MECD projects still show "ER simulation not yet available" warning in the simulator tab. The backend fully supports MECD simulation; enabling the UI tab requires adding MECD-specific parameter override inputs (case, baseline_fuels, project_fuel_type, etc.).
- **LPG/electric VM0050 params**: `EC_electricity_project`, `EF_electricity`, `TDL` are defined in the parameter engine for electric cookstove projects but the `calculate_cookstove_er` calculator does not currently use them (it uses `project_fuel_consumption` regardless). These params are extracted from documents but do not influence the ER calculation.
- **Grid year-table col 3 fallback**: In `er_excel.py`, if `eg_pj_cell` is None for a grid project, the formula fallback divides `baseline_emissions_annual / itself`, which would produce 1.0 instead of the static EG_PJ value.

## ER Excel Workbook — Formula Traceability (Deep Audit 2026-03)

The `generate_exante_workbook()` function in `carbongpt/core/er_excel.py` now produces a **fully traceable workbook** with no hardcoded values:

**Parameters tab**: All input parameters in column C (source, tier, conservativeness). Now includes `UR_decay` and `UR_floor` which were previously skipped. `bl_consumption_wood_equiv` is excluded (it's a derived intermediate shown in calc steps).

**ER Calculation tab**: Every Result cell (col D) in the step-by-step section is a live Excel formula:
- D6: `=Parameters!C{row}` — baseline fuel consumption (SFC_b)
- D7: `=Parameters!C{row}` — project fuel consumption (SFC_p)
- D8: CF-adjusted baseline (wood = D6 directly; charcoal = D6 × CF)
- D9: `=D8 × NCV_b / 1000` — baseline energy (TJ)
- D10: `=D9 × (fNRB × EF_CO2_b + EF_nonCO2_b)` — BE per device
- D11: `=D7 × NCV_p / 1000` — project energy (Method 3 adds CF)
- D12: `=D11 × (fNRB × EF_CO2_p + EF_nonCO2_p)` (Method 1/2), or `×(EF_CO2_p + EF_nonCO2_p)` (Method 3, no fNRB on PE)
- D13: `=D10-D12` — ER per device before leakage

Annual year table cells are all formulas:
- Active devices: `=MAX(UR − (Y−1)×decay, floor) × N` — references Parameters decay and floor
- Baseline: `=D10 × C{row}` — BE_per_device × active_devices
- Project: `=D12 × C{row}` — PE_per_device × active_devices
- Gross ER: `=Baseline − Project`
- Leakage: `=Gross_ER × leakage_pct` — references Parameters leakage cell
- Net ER: `=Gross_ER − Leakage`

**Vintage Table tab**: All values are cross-sheet references to ER Calculation (`='ER Calculation'!D{row}`, etc.).

**Parameter UI improvements (`carbongpt/ui/parameter_ui.py`)**:
- Method 2: SFC_baseline now hidden from editable Parameters list (locked by methodology default); shown in an `st.info` banner with the computed value
- `bl_consumption_wood_equiv` added to `DERIVED_PARAMS` (shows as derived, not editable)
- `fNRB` parameter renders a guidance caption about country-specific sources (IPCC defaults, GS/CDM approved studies)
- `_should_show_param()` updated to hide Method 2 locked params

## Startup & Deployment Notes

- **FastAPI startup time**: The backend takes ~45 seconds on first boot to run schema migrations, country normalization, and registry seeding. Streamlit is ready immediately.
- **Startup health check**: `streamlit_app.py` pings `GET /health` before rendering the UI. While FastAPI is initialising, a clean "Starting up..." screen is shown with auto-retry (every 3 s, up to 60 s). This prevents scattered connection errors from appearing throughout the UI.
- **API base URL**: Controlled by `CARBONGPT_API_URL` env var (default: `http://localhost:3000`). Can be overridden in the deployment environment if needed.
- **Deployment command**: `bash start_carbongpt.sh` — starts Streamlit (background, port 5000) and FastAPI via `exec uvicorn` (port 3000). Both run in the same VM.

## External Dependencies

-   **PostgreSQL:** Primary relational database.
-   **pgvector:** PostgreSQL extension for vector similarity search.
-   **OpenAI API:** For LLM inference (GPT-4o, GPT-4o-mini) and embeddings (text-embedding-3-small).
-   **Serper.dev API:** Used for web search to verify methodology status.
-   **Verra REST API:** Accesses registry project metadata and methodology PDFs.
-   **Gold Standard API:** Retrieves project data and document templates.
-   **UNFCCC/CDM resources:** Provides CDM methodology booklets and tools.