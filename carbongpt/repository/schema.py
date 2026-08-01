import logging
from carbongpt.repository.db import get_cursor

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS standards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS standard_versions (
    id SERIAL PRIMARY KEY,
    standard_id INTEGER NOT NULL REFERENCES standards(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    effective_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'draft')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(standard_id, version)
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    standard_version_id INTEGER REFERENCES standard_versions(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'standard_text', 'methodology', 'guidance', 'tool',
        'template', 'example_pdd', 'example_mr', 'example_fvr',
        'example_valver', 'example_other', 'rule_update',
        'rule_clarification', 'deviation', 'clarification_request', 'other'
    )),
    title VARCHAR(500) NOT NULL,
    reference_id VARCHAR(100),
    doc_version VARCHAR(50),
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'xlsx', 'csv', 'other')),
    file_size_bytes INTEGER,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'archived')),
    auto_detected_standard VARCHAR(200),
    auto_detected_version VARCHAR(100),
    auto_detected_category VARCHAR(100),
    auto_detected_applicability TEXT,
    ingestion_status VARCHAR(20) DEFAULT 'pending' CHECK (ingestion_status IN ('pending', 'processing', 'completed', 'failed', 'unsupported')),
    ingestion_error TEXT,
    page_count INTEGER,
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_sections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_number VARCHAR(20),
    title VARCHAR(500),
    content TEXT NOT NULL,
    parent_section_id INTEGER REFERENCES document_sections(id) ON DELETE SET NULL,
    section_order INTEGER DEFAULT 0,
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_id INTEGER REFERENCES document_sections(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_references (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    reference_type VARCHAR(50) DEFAULT 'references',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_rules (
    id SERIAL PRIMARY KEY,
    standard_id INTEGER REFERENCES standards(id) ON DELETE SET NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN (
        'methodology_status', 'methodology_transition',
        'crediting_period', 'eligibility', 'regulatory',
        'default_value', 'fee_structure', 'general'
    )),
    severity VARCHAR(20) NOT NULL DEFAULT 'error' CHECK (severity IN ('error', 'warning', 'info')),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    conditions JSONB NOT NULL DEFAULT '{}',
    effective_date DATE,
    expiry_date DATE,
    source_url TEXT,
    source_description VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'proposed', 'expired', 'rejected')),
    discovered_by VARCHAR(50) DEFAULT 'manual' CHECK (discovered_by IN ('manual', 'ai_review', 'web_search', 'admin')),
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbon_projects (
    id SERIAL PRIMARY KEY,
    registry VARCHAR(20) NOT NULL,
    registry_id VARCHAR(50) NOT NULL,
    name VARCHAR(500) NOT NULL,
    status VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(100),
    proponent VARCHAR(300),
    methodology VARCHAR(300),
    project_type VARCHAR(200),
    project_subtype VARCHAR(300),
    estimated_annual_credits INTEGER,
    crediting_period_start DATE,
    crediting_period_end DATE,
    registration_date DATE,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    description TEXT,
    sdgs TEXT,
    extra_data JSONB DEFAULT '{}',
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(registry, registry_id)
);

CREATE INDEX IF NOT EXISTS idx_carbon_projects_registry ON carbon_projects(registry);
CREATE INDEX IF NOT EXISTS idx_carbon_projects_country ON carbon_projects(country);
CREATE INDEX IF NOT EXISTS idx_carbon_projects_region ON carbon_projects(region);
CREATE INDEX IF NOT EXISTS idx_carbon_projects_status ON carbon_projects(status);
CREATE INDEX IF NOT EXISTS idx_carbon_projects_project_type ON carbon_projects(project_type);

CREATE TABLE IF NOT EXISTS user_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    standard VARCHAR(50) NOT NULL,
    doc_type VARCHAR(50),
    methodology VARCHAR(300),
    country VARCHAR(100),
    description TEXT,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'under_review', 'submitted', 'registered', 'archived')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN (
        'pdd', 'mr', 'valver', 'poa_dd', 'vpa_dd',
        'reference', 'research', 'field_data', 'template', 'other'
    )),
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'xlsx', 'csv', 'other')),
    file_size_bytes INTEGER,
    parsed_text TEXT,
    parsed_sections JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'parsed', 'reviewed', 'draft_generated')),
    review_result JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_write_sessions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    section_id VARCHAR(20) NOT NULL,
    section_title VARCHAR(300),
    generated_text TEXT,
    user_text TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'needs_revision')),
    ai_context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS methodologies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(500),
    short_name VARCHAR(100),
    former_name VARCHAR(200),
    standard VARCHAR(50),
    category VARCHAR(100),
    sector VARCHAR(200),
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'under_revision', 'draft', 'withdrawn')),
    applicability TEXT,
    description TEXT,
    source_url TEXT,
    superseded_by VARCHAR(50),
    project_count INTEGER DEFAULT 0,
    last_checked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS methodology_parsed (
    id SERIAL PRIMARY KEY,
    methodology_code VARCHAR(100) NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    parsed_data JSONB NOT NULL,
    model_used VARCHAR(50),
    parse_status VARCHAR(20) DEFAULT 'completed' CHECK (parse_status IN ('pending', 'processing', 'completed', 'failed')),
    parse_error TEXT,
    parsed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(methodology_code)
);

CREATE INDEX IF NOT EXISTS idx_methodology_parsed_code ON methodology_parsed(methodology_code);
CREATE INDEX IF NOT EXISTS idx_methodology_parsed_status ON methodology_parsed(parse_status);

CREATE INDEX IF NOT EXISTS idx_methodologies_standard ON methodologies(standard);
CREATE INDEX IF NOT EXISTS idx_methodologies_category ON methodologies(category);
CREATE INDEX IF NOT EXISTS idx_methodologies_status ON methodologies(status);
CREATE INDEX IF NOT EXISTS idx_methodologies_code ON methodologies(code);

CREATE INDEX IF NOT EXISTS idx_user_projects_standard ON user_projects(standard);
CREATE INDEX IF NOT EXISTS idx_user_projects_status ON user_projects(status);
CREATE INDEX IF NOT EXISTS idx_project_documents_project ON project_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_project_documents_doc_type ON project_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_project_write_sessions_project ON project_write_sessions(project_id);

ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS crediting_period_start DATE;
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS crediting_period_years INTEGER DEFAULT 7;
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS project_settings JSONB DEFAULT '{}';
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS project_intake JSONB DEFAULT '{}';
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(30) DEFAULT 'standalone_pdd';
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS parent_project_id INTEGER REFERENCES user_projects(id) ON DELETE SET NULL;
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS monitoring_period_start DATE;
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS monitoring_period_end DATE;

ALTER TABLE project_documents ADD COLUMN IF NOT EXISTS use_as_ai_context BOOLEAN DEFAULT true;
ALTER TABLE project_documents ADD COLUMN IF NOT EXISTS ai_extracted_summary TEXT;
ALTER TABLE project_documents ADD COLUMN IF NOT EXISTS ai_extracted_data JSONB;

CREATE INDEX IF NOT EXISTS idx_user_projects_parent ON user_projects(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_user_projects_project_type ON user_projects(project_type);

ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS search_vector tsvector;

ALTER TABLE document_sections ADD COLUMN IF NOT EXISTS section_path TEXT;

ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_documents_standard_version ON documents(standard_version_id);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_ingestion_status ON documents(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_documents_reference_id ON documents(reference_id);
CREATE INDEX IF NOT EXISTS idx_documents_search_vector ON documents USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_document_sections_document ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_document_chunks_search_vector ON document_chunks USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_standard ON compliance_rules(standard_id);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_type ON compliance_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_status ON compliance_rules(status);

CREATE TABLE IF NOT EXISTS methodology_knowledge (
    id SERIAL PRIMARY KEY,
    methodology_code VARCHAR(100) NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    chunk_type VARCHAR(50) NOT NULL CHECK (chunk_type IN (
        'applicability', 'method_selection', 'equations', 'parameters',
        'default_values', 'sampling', 'monitoring', 'safeguards',
        'tools_referenced', 'definitions', 'leakage', 'quantification', 'general'
    )),
    chunk_key VARCHAR(200) NOT NULL,
    title VARCHAR(500),
    content TEXT NOT NULL,
    structured_data JSONB DEFAULT '{}',
    source_section_ids INTEGER[],
    extraction_method VARCHAR(30) DEFAULT 'programmatic' CHECK (extraction_method IN ('programmatic', 'ai_assisted', 'manual')),
    confidence REAL DEFAULT 1.0,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(methodology_code, chunk_type, chunk_key)
);

CREATE TABLE IF NOT EXISTS project_doc_chunks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    doc_id INTEGER NOT NULL REFERENCES project_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(1536),
    section_title VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pdc_project ON project_doc_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_pdc_doc ON project_doc_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_pdc_search_vector ON project_doc_chunks USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_mk_methodology_code ON methodology_knowledge(methodology_code);
CREATE INDEX IF NOT EXISTS idx_mk_chunk_type ON methodology_knowledge(chunk_type);
CREATE INDEX IF NOT EXISTS idx_mk_document_id ON methodology_knowledge(document_id);

CREATE TABLE IF NOT EXISTS methodology_structure (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    methodology_code VARCHAR(100),
    detected_format JSONB NOT NULL DEFAULT '{}',
    section_map JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ms_methodology_code ON methodology_structure(methodology_code);

CREATE TABLE IF NOT EXISTS findings_knowledge (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    methodology_code VARCHAR(100),
    finding_type VARCHAR(20) NOT NULL CHECK (finding_type IN ('CAR', 'CL', 'FAR', 'observation', 'comment', 'prr_comment')),
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    pdd_section VARCHAR(100),
    topic VARCHAR(200),
    description TEXT NOT NULL,
    resolution TEXT,
    resolution_approach VARCHAR(50),
    standard VARCHAR(50),
    doc_type VARCHAR(50),
    vvb_name VARCHAR(200),
    source_project_id VARCHAR(100),
    source_project_name VARCHAR(300),
    structured_data JSONB DEFAULT '{}',
    extraction_method VARCHAR(30) DEFAULT 'ai_assisted' CHECK (extraction_method IN ('programmatic', 'ai_assisted', 'manual')),
    confidence REAL DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fk_methodology ON findings_knowledge(methodology_code);
CREATE INDEX IF NOT EXISTS idx_fk_finding_type ON findings_knowledge(finding_type);
CREATE INDEX IF NOT EXISTS idx_fk_pdd_section ON findings_knowledge(pdd_section);
CREATE INDEX IF NOT EXISTS idx_fk_source_doc ON findings_knowledge(source_document_id);
CREATE INDEX IF NOT EXISTS idx_fk_topic ON findings_knowledge(topic);

CREATE TABLE IF NOT EXISTS research_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    research_layer VARCHAR(50) NOT NULL CHECK (research_layer IN (
        'general_context', 'methodology_rules', 'technical_parameters',
        'project_documents', 'knowledge_base', 'regulatory_web',
        'dependencies', 'compliance'
    )),
    field_path VARCHAR(200),
    query TEXT NOT NULL,
    result_data JSONB DEFAULT '{}',
    sources JSONB DEFAULT '[]',
    confidence REAL DEFAULT 0.5,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rr_project ON research_results(project_id);
CREATE INDEX IF NOT EXISTS idx_rr_status ON research_results(status);
CREATE INDEX IF NOT EXISTS idx_rr_layer ON research_results(research_layer);

CREATE TABLE IF NOT EXISTS research_source_priority (
    id SERIAL PRIMARY KEY,
    methodology_code VARCHAR(100),
    parameter_name VARCHAR(200),
    source_rank INTEGER NOT NULL DEFAULT 1,
    source_type VARCHAR(100) NOT NULL,
    source_description TEXT,
    is_admissible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rsp_meth ON research_source_priority(methodology_code);
CREATE INDEX IF NOT EXISTS idx_rsp_param ON research_source_priority(parameter_name);

INSERT INTO standards (name, slug, description) VALUES
    ('Gold Standard', 'goldstandard', 'Gold Standard for the Global Goals - carbon credit certification'),
    ('Verra VCS', 'verra', 'Verified Carbon Standard by Verra - voluntary carbon market')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO standard_versions (standard_id, version, effective_date, status) VALUES
    ((SELECT id FROM standards WHERE slug = 'goldstandard'), '1.x', '2020-01-01', 'active'),
    ((SELECT id FROM standards WHERE slug = 'verra'), '4.4', '2023-01-01', 'active')
ON CONFLICT (standard_id, version) DO NOTHING;

-- ============================================================
-- CARBON OPERATING SYSTEM TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS project_parameters (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    param_key VARCHAR(100) NOT NULL,
    param_name VARCHAR(300) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'baseline', 'project', 'monitoring', 'leakage', 'emission_factor',
        'fuel_property', 'activity_data', 'calculated', 'financial', 'other'
    )),
    value TEXT,
    unit VARCHAR(100),
    data_type VARCHAR(20) DEFAULT 'number' CHECK (data_type IN ('number', 'text', 'date', 'boolean', 'percentage')),
    source_type VARCHAR(30) DEFAULT 'default' CHECK (source_type IN (
        'default', 'measured', 'calculated', 'user_override', 'national_inventory', 'ipcc', 'methodology', 'document_extracted'
    )),
    source_reference TEXT,
    evidence_doc_id INTEGER REFERENCES project_documents(id) ON DELETE SET NULL,
    evidence_detail TEXT,
    methodology_code VARCHAR(100),
    tool_reference VARCHAR(100),
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('valid', 'invalid', 'pending', 'warning')),
    validation_message TEXT,
    param_status VARCHAR(20) DEFAULT 'default' CHECK (param_status IN ('confirmed', 'default', 'estimated', 'missing')),
    is_ex_ante BOOLEAN DEFAULT true,
    uncertainty_pct DOUBLE PRECISION,
    depends_on TEXT[],
    year_specific BOOLEAN DEFAULT false,
    applicable_year INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, param_key, applicable_year)
);

CREATE INDEX IF NOT EXISTS idx_pp_project ON project_parameters(project_id);
CREATE INDEX IF NOT EXISTS idx_pp_category ON project_parameters(category);
CREATE INDEX IF NOT EXISTS idx_pp_key ON project_parameters(param_key);
CREATE INDEX IF NOT EXISTS idx_pp_validation ON project_parameters(validation_status);

CREATE TABLE IF NOT EXISTS project_lifecycle (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL CHECK (stage IN (
        'feasibility', 'pdd_design', 'internal_review', 'validation',
        'registration', 'monitoring', 'verification', 'issuance', 'closed'
    )),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'skipped')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pl_project ON project_lifecycle(project_id);
CREATE INDEX IF NOT EXISTS idx_pl_stage ON project_lifecycle(stage);

CREATE TABLE IF NOT EXISTS project_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    lifecycle_stage VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) DEFAULT 'general' CHECK (task_type IN (
        'general', 'document', 'data_collection', 'review', 'submission',
        'monitoring', 'verification', 'stakeholder', 'financial'
    )),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
    due_date DATE,
    completed_at TIMESTAMP,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pt_project ON project_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_pt_stage ON project_tasks(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_pt_status ON project_tasks(status);

CREATE TABLE IF NOT EXISTS evidence_links (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    target_type VARCHAR(30) NOT NULL CHECK (target_type IN ('parameter', 'section', 'claim')),
    target_id VARCHAR(200) NOT NULL,
    target_description TEXT,
    source_type VARCHAR(30) NOT NULL CHECK (source_type IN (
        'project_document', 'methodology', 'tool', 'external', 'calculation', 'field_data'
    )),
    source_doc_id INTEGER,
    source_chunk_id INTEGER,
    source_title VARCHAR(500),
    source_detail TEXT,
    page_number INTEGER,
    table_reference VARCHAR(100),
    quote TEXT,
    confidence REAL DEFAULT 1.0,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    extracted_value TEXT,
    extracted_unit VARCHAR(50),
    param_key VARCHAR(100),
    evidence_type VARCHAR(30) DEFAULT 'parameter_value',
    evidence_decision VARCHAR(30) DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_el_project ON evidence_links(project_id);
CREATE INDEX IF NOT EXISTS idx_el_target ON evidence_links(target_type, target_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_el_dedup_pending
    ON evidence_links (project_id, source_doc_id, param_key, extracted_value, COALESCE(source_detail, ''))
    WHERE evidence_decision = 'pending' AND evidence_type = 'parameter_value';

CREATE TABLE IF NOT EXISTS er_scenarios (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    description TEXT,
    is_baseline BOOLEAN DEFAULT false,
    parameter_overrides JSONB DEFAULT '{}',
    methodology_code VARCHAR(100),
    crediting_years INTEGER DEFAULT 7,
    carbon_price_usd DOUBLE PRECISION,
    price_escalation_pct DOUBLE PRECISION DEFAULT 0,
    developer_share_pct DOUBLE PRECISION DEFAULT 100,
    buffer_pool_pct DOUBLE PRECISION DEFAULT 0,
    admin_fee_pct DOUBLE PRECISION DEFAULT 0,
    results_summary JSONB DEFAULT '{}',
    calculated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ers_project ON er_scenarios(project_id);

CREATE TABLE IF NOT EXISTS er_scenario_years (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER NOT NULL REFERENCES er_scenarios(id) ON DELETE CASCADE,
    year_number INTEGER NOT NULL,
    calendar_year INTEGER,
    baseline_emissions DOUBLE PRECISION DEFAULT 0,
    project_emissions DOUBLE PRECISION DEFAULT 0,
    leakage DOUBLE PRECISION DEFAULT 0,
    net_er DOUBLE PRECISION DEFAULT 0,
    gross_revenue DOUBLE PRECISION DEFAULT 0,
    deductions DOUBLE PRECISION DEFAULT 0,
    net_revenue DOUBLE PRECISION DEFAULT 0,
    details JSONB DEFAULT '{}',
    UNIQUE(scenario_id, year_number)
);

CREATE INDEX IF NOT EXISTS idx_esy_scenario ON er_scenario_years(scenario_id);

CREATE TABLE IF NOT EXISTS issuance_records (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    vintage_year INTEGER NOT NULL,
    monitoring_period_start DATE,
    monitoring_period_end DATE,
    verification_date DATE,
    issuance_date DATE,
    credits_requested DOUBLE PRECISION,
    credits_issued DOUBLE PRECISION,
    buffer_contribution DOUBLE PRECISION,
    registry_serial_start VARCHAR(100),
    registry_serial_end VARCHAR(100),
    registry_status VARCHAR(30) DEFAULT 'planned' CHECK (registry_status IN (
        'planned', 'monitoring', 'under_verification', 'verified', 'issued', 'retired', 'cancelled'
    )),
    vvb_name VARCHAR(300),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ir_project ON issuance_records(project_id);
CREATE INDEX IF NOT EXISTS idx_ir_vintage ON issuance_records(vintage_year);
CREATE INDEX IF NOT EXISTS idx_ir_status ON issuance_records(registry_status);

CREATE TABLE IF NOT EXISTS monitoring_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    param_key VARCHAR(100),
    task_name VARCHAR(500) NOT NULL,
    description TEXT,
    frequency VARCHAR(50) DEFAULT 'annual' CHECK (frequency IN (
        'continuous', 'daily', 'weekly', 'monthly', 'quarterly',
        'semi_annual', 'annual', 'biennial', 'once', 'per_crediting_period'
    )),
    method VARCHAR(200),
    responsible_party VARCHAR(200),
    qaqc_procedure TEXT,
    next_due_date DATE,
    last_completed_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'overdue')),
    monitoring_period INTEGER,
    data_collected JSONB DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mt_project ON monitoring_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_mt_status ON monitoring_tasks(status);

CREATE TABLE IF NOT EXISTS audit_simulation_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    simulation_type VARCHAR(30) DEFAULT 'full' CHECK (simulation_type IN ('full', 'parameters', 'evidence', 'consistency', 'compliance')),
    overall_score INTEGER DEFAULT 0,
    risk_level VARCHAR(20) DEFAULT 'UNKNOWN' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN')),
    findings JSONB DEFAULT '[]',
    summary TEXT,
    parameter_issues JSONB DEFAULT '[]',
    evidence_gaps JSONB DEFAULT '[]',
    consistency_issues JSONB DEFAULT '[]',
    compliance_issues JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    simulated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asr_project ON audit_simulation_results(project_id);

-- Phase 2a: Scenario purpose lifecycle + selected scenario reference
ALTER TABLE er_scenarios ADD COLUMN IF NOT EXISTS scenario_purpose VARCHAR(30) DEFAULT 'exploratory';
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS selected_scenario_id INTEGER;

CREATE TABLE IF NOT EXISTS section_exemplars (
    id SERIAL PRIMARY KEY,
    document_section_id INTEGER NOT NULL REFERENCES document_sections(id),
    document_id INTEGER NOT NULL REFERENCES documents(id),
    doc_type VARCHAR(20) NOT NULL,
    standard VARCHAR(30),
    methodology_code VARCHAR(30),
    project_type VARCHAR(30),
    section_domain VARCHAR(30) NOT NULL CHECK (section_domain IN (
        'baseline', 'additionality', 'monitoring', 'sampling'
    )),
    section_title TEXT,
    section_purpose VARCHAR(40),
    is_usable BOOLEAN NOT NULL DEFAULT true,
    word_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exemplars_domain ON section_exemplars(section_domain);
CREATE INDEX IF NOT EXISTS idx_exemplars_lookup ON section_exemplars(section_domain, standard, project_type)
    WHERE is_usable = true;

-- ============================================================
-- CARBON INTELLIGENCE — NORMALIZATION LAYER (Step 1 + 2)
-- ============================================================

CREATE TABLE IF NOT EXISTS methodology_library (
    methodology_code   VARCHAR(30)  PRIMARY KEY,
    display_name       VARCHAR(200) NOT NULL,
    methodology_family VARCHAR(100),
    registry           VARCHAR(30)  DEFAULT 'Any',
    sector             VARCHAR(100),
    technology         VARCHAR(100),
    status             VARCHAR(20)  DEFAULT 'active',
    notes              TEXT
);

CREATE TABLE IF NOT EXISTS project_methodology_codes (
    id                SERIAL PRIMARY KEY,
    project_id        INTEGER NOT NULL REFERENCES carbon_projects(id) ON DELETE CASCADE,
    methodology_code  VARCHAR(30) NOT NULL REFERENCES methodology_library(methodology_code),
    is_primary        BOOLEAN DEFAULT TRUE,
    raw_segment       VARCHAR(300),
    UNIQUE(project_id, methodology_code)
);

CREATE INDEX IF NOT EXISTS idx_pmc_project  ON project_methodology_codes(project_id);
CREATE INDEX IF NOT EXISTS idx_pmc_code     ON project_methodology_codes(methodology_code);

CREATE TABLE IF NOT EXISTS methodology_normalization_log (
    id               SERIAL PRIMARY KEY,
    raw_string       VARCHAR(300) NOT NULL UNIQUE,
    raw_segment      VARCHAR(300),
    occurrence_count INTEGER   DEFAULT 1,
    first_seen       TIMESTAMP DEFAULT NOW(),
    last_seen        TIMESTAMP DEFAULT NOW(),
    resolved_code    VARCHAR(30),
    status           VARCHAR(20) DEFAULT 'unknown' CHECK (status IN ('unknown', 'resolved', 'ignored'))
);

CREATE TABLE IF NOT EXISTS countries (
    country_iso   CHAR(3)      PRIMARY KEY,
    country_name  VARCHAR(100) NOT NULL,
    region        VARCHAR(50),
    subregion     VARCHAR(80)
);

ALTER TABLE carbon_projects ADD COLUMN IF NOT EXISTS country_iso CHAR(3) REFERENCES countries(country_iso);

-- ============================================================
-- Step 1 of the shared-core architecture: ref_registries
-- Canonical registry reference table.  Existing raw `registry`
-- column on carbon_projects is kept for auditability.
-- ref_registry_id is the FK to this table, populated by the
-- registry normalizer after each sync.
-- ============================================================

CREATE TABLE IF NOT EXISTS ref_registries (
    registry_id    VARCHAR(30)  PRIMARY KEY,
    registry_name  VARCHAR(200) NOT NULL,
    registry_short VARCHAR(30)  NOT NULL,
    website        VARCHAR(300),
    created_at     TIMESTAMP    DEFAULT NOW()
);

ALTER TABLE carbon_projects
    ADD COLUMN IF NOT EXISTS ref_registry_id VARCHAR(30)
    REFERENCES ref_registries(registry_id);

CREATE INDEX IF NOT EXISTS idx_carbon_projects_ref_registry
    ON carbon_projects(ref_registry_id);

-- ============================================================
-- Shared-core Wave 2: canonical methodology reference table.
-- Existing methodology_library, methodology_parsed, and
-- project_methodology_codes tables are kept unchanged.
-- ref_methodologies is the new authoritative reference.
-- ============================================================

CREATE TABLE IF NOT EXISTS ref_methodologies (
    methodology_code   VARCHAR(50)  PRIMARY KEY,
    methodology_name   VARCHAR(400),
    methodology_family VARCHAR(100),
    ref_registry_id    VARCHAR(30)  REFERENCES ref_registries(registry_id),
    sector             VARCHAR(100),
    technology         VARCHAR(100),
    status             VARCHAR(20)  DEFAULT 'active',
    aliases            TEXT[],
    version            VARCHAR(30),
    notes              TEXT,
    created_at         TIMESTAMP    DEFAULT NOW(),
    updated_at         TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ref_methodologies_family
    ON ref_methodologies(methodology_family);
CREATE INDEX IF NOT EXISTS idx_ref_methodologies_registry
    ON ref_methodologies(ref_registry_id);
CREATE INDEX IF NOT EXISTS idx_ref_methodologies_sector
    ON ref_methodologies(sector);

-- ============================================================
-- Shared-core Wave 2: extend countries table with aliases.
-- Allows both surfaces to query "find country by any alias"
-- without maintaining separate Python dicts.
-- ============================================================

ALTER TABLE countries ADD COLUMN IF NOT EXISTS aliases TEXT[];

-- ============================================================
-- Shared-core Wave 2: add country_iso FK to user_projects
-- so CarbonGPT project setup uses the same canonical country
-- layer as Carbon Intelligence.
-- ============================================================

ALTER TABLE user_projects
    ADD COLUMN IF NOT EXISTS country_iso CHAR(3)
    REFERENCES countries(country_iso);

CREATE INDEX IF NOT EXISTS idx_user_projects_country_iso
    ON user_projects(country_iso);

-- ============================================================
-- Shared-core Wave 2: issuance groundwork.
-- Stores actual verified/issued credit events per project.
-- This table is intentionally empty until stable issuance
-- sources are confirmed; it is NOT populated by any sync yet.
-- Estimated annual credits (on carbon_projects) remain the
-- primary planning figure; this table will hold actuals.
-- ============================================================

CREATE TABLE IF NOT EXISTS project_issuance (
    id                  SERIAL       PRIMARY KEY,
    registry_project_id VARCHAR(100) NOT NULL,
    registry            VARCHAR(50)  NOT NULL,
    ref_registry_id     VARCHAR(30)  REFERENCES ref_registries(registry_id),
    vintage_year        INTEGER,
    issuance_date       DATE,
    verified_credits    BIGINT,
    retired_credits     BIGINT,
    status              VARCHAR(30),
    source_label        VARCHAR(100),
    notes               TEXT,
    raw_data            JSONB,
    synced_at           TIMESTAMP    DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_issuance_unique
    ON project_issuance(registry_project_id, registry, vintage_year, issuance_date);
CREATE INDEX IF NOT EXISTS idx_project_issuance_registry
    ON project_issuance(registry);
CREATE INDEX IF NOT EXISTS idx_project_issuance_vintage
    ON project_issuance(vintage_year);

-- ============================================================
-- METHODOLOGY PACK MANAGER
-- Curated, versioned knowledge packs that ground CarbonGPT
-- AI responses in real approved-project precedent.
-- Reuses the existing documents + document_chunks system.
-- ============================================================

CREATE TABLE IF NOT EXISTS methodology_packs (
    id                       SERIAL       PRIMARY KEY,
    methodology_code         VARCHAR(50)  NOT NULL,
    methodology_family       VARCHAR(100),
    registry                 VARCHAR(30)  NOT NULL,
    methodology_version      VARCHAR(30),
    version_valid_from       DATE,
    version_valid_to         DATE,
    indexing_status          VARCHAR(30)  NOT NULL DEFAULT 'not_started'
        CHECK (indexing_status IN (
            'not_started', 'collecting_documents', 'ready_for_indexing',
            'indexed', 'needs_update', 'archived'
        )),
    pdd_count                INTEGER      DEFAULT 0,
    mr_count                 INTEGER      DEFAULT 0,
    validation_count         INTEGER      DEFAULT 0,
    tool_doc_count           INTEGER      DEFAULT 0,
    target_pdd_count         INTEGER      DEFAULT 30,
    target_mr_count          INTEGER      DEFAULT 5,
    target_validation_count  INTEGER      DEFAULT 3,
    readiness_score          INTEGER      DEFAULT 0,
    readiness_gates_passed   JSONB        DEFAULT '{}',
    notes                    TEXT,
    created_by               TEXT,
    created_at               TIMESTAMPTZ  DEFAULT NOW(),
    last_updated             TIMESTAMPTZ  DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_packs_unique_code_registry_version
    ON methodology_packs (methodology_code, registry, COALESCE(methodology_version, ''));
CREATE INDEX IF NOT EXISTS idx_packs_methodology ON methodology_packs(methodology_code);
CREATE INDEX IF NOT EXISTS idx_packs_status     ON methodology_packs(indexing_status);
CREATE INDEX IF NOT EXISTS idx_packs_registry   ON methodology_packs(registry);

-- Junction table: links existing documents to a pack with role metadata.
-- Reuses the full documents + document_chunks storage — no second chunk store.
CREATE TABLE IF NOT EXISTS methodology_pack_document_links (
    id                   SERIAL       PRIMARY KEY,
    pack_id              INTEGER      NOT NULL REFERENCES methodology_packs(id) ON DELETE CASCADE,
    document_id          INTEGER      NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_role        VARCHAR(30)  NOT NULL
        CHECK (document_role IN (
            'METHODOLOGY_DOC', 'TOOL_DOC', 'GUIDANCE_DOC', 'TEMPLATE',
            'PDD', 'MR', 'VALIDATION_REPORT', 'VERIFICATION_REPORT',
            'DEVIATION_REPORT', 'DOE_FINDING'
        )),
    project_id           INTEGER      REFERENCES carbon_projects(id) ON DELETE SET NULL,
    project_registry_id  VARCHAR(100),
    methodology_version  VARCHAR(30),
    vintage_year         INTEGER,
    validation_body      VARCHAR(200),
    added_by             TEXT,
    added_at             TIMESTAMPTZ  DEFAULT NOW(),
    quality_flags        JSONB        DEFAULT '{}',
    UNIQUE (pack_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_mpdl_pack     ON methodology_pack_document_links(pack_id);
CREATE INDEX IF NOT EXISTS idx_mpdl_document ON methodology_pack_document_links(document_id);
CREATE INDEX IF NOT EXISTS idx_mpdl_role     ON methodology_pack_document_links(pack_id, document_role);

-- Structured DOE findings: CARs, CLs, FARs, review comments.
-- Populated by AI extraction during ingestion OR by admin manual entry.
CREATE TABLE IF NOT EXISTS pack_findings (
    id                      SERIAL       PRIMARY KEY,
    pack_id                 INTEGER      NOT NULL REFERENCES methodology_packs(id) ON DELETE CASCADE,
    source_link_id          INTEGER      REFERENCES methodology_pack_document_links(id) ON DELETE SET NULL,
    finding_type            VARCHAR(20)  NOT NULL
        CHECK (finding_type IN ('CAR', 'CL', 'FAR', 'CR', 'REVIEW_COMMENT')),
    finding_reference       VARCHAR(50),
    section_reference       VARCHAR(200),
    finding_text            TEXT         NOT NULL,
    response_text           TEXT,
    resolution_status       VARCHAR(25)  DEFAULT 'closed'
        CHECK (resolution_status IN ('open', 'closed', 'pending_next_period')),
    finding_vintage         INTEGER,
    validation_body         VARCHAR(200),
    extracted_automatically BOOLEAN      DEFAULT FALSE,
    created_at              TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pf_pack ON pack_findings(pack_id);
CREATE INDEX IF NOT EXISTS idx_pf_type ON pack_findings(pack_id, finding_type);

-- Version history: used by the monthly monitor job to detect new methodology versions.
CREATE TABLE IF NOT EXISTS methodology_version_history (
    id                SERIAL       PRIMARY KEY,
    methodology_code  VARCHAR(50)  NOT NULL,
    registry          VARCHAR(30)  NOT NULL,
    version           VARCHAR(30)  NOT NULL,
    released_date     DATE,
    effective_from    DATE,
    effective_until   DATE,
    is_current        BOOLEAN      DEFAULT FALSE,
    paris_aligned     BOOLEAN      DEFAULT FALSE,
    document_name     VARCHAR(300),
    pdf_url           TEXT,
    local_path        TEXT,
    detected_at       TIMESTAMPTZ  DEFAULT NOW(),
    source_url        TEXT,
    content_hash      VARCHAR(64),
    status            VARCHAR(20)  DEFAULT 'active'
        CHECK (status IN ('active', 'superseded', 'retired')),
    superseded_by     VARCHAR(30),
    pack_id           INTEGER      REFERENCES methodology_packs(id) ON DELETE SET NULL,
    UNIQUE (methodology_code, registry, version)
);

CREATE INDEX IF NOT EXISTS idx_mvh_methodology ON methodology_version_history(methodology_code, registry);

-- ============================================================
-- Reusable profiles: technology, developer, participant
-- ============================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id           SERIAL       PRIMARY KEY,
    profile_type VARCHAR(30)  NOT NULL CHECK (profile_type IN ('technology', 'developer', 'participant')),
    name         VARCHAR(200) NOT NULL,
    description  TEXT,
    data         JSONB        NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_type ON user_profiles(profile_type);

-- ============================================================
-- SPEC-01 -- Corpus reglementaire versionne (docs/SPEC-01.md)
--
-- Migration additive : etend methodologies, methodology_version_history
-- et documents (nouvelles colonnes nullable uniquement, rien de supprime
-- ni de modifie) ; cree regulatory_values, qui n'a pas d'equivalent
-- existant. Voir docs/DECISIONS.md pour la justification.
-- ============================================================

ALTER TABLE methodologies ADD COLUMN IF NOT EXISTS short_name VARCHAR(100);
ALTER TABLE methodologies ADD COLUMN IF NOT EXISTS former_name VARCHAR(200);
ALTER TABLE methodologies ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP;

ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS released_date DATE;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS effective_from DATE;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS effective_until DATE;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS paris_aligned BOOLEAN DEFAULT FALSE;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS document_name VARCHAR(300);
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS pdf_url TEXT;
ALTER TABLE methodology_version_history ADD COLUMN IF NOT EXISTS local_path TEXT;

-- Widen the category check to cover the related-document types SPEC-01
-- needs (rule_clarification, deviation, clarification_request). Only
-- adds allowed values, so every existing row still satisfies it.
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_category_check;
ALTER TABLE documents ADD CONSTRAINT documents_category_check CHECK (category IN (
    'standard_text', 'methodology', 'guidance', 'tool',
    'template', 'example_pdd', 'example_mr', 'example_fvr',
    'example_valver', 'example_other', 'rule_update',
    'rule_clarification', 'deviation', 'clarification_request', 'other'
));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS methodology_version_id INTEGER
    REFERENCES methodology_version_history(id) ON DELETE SET NULL;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_documents_methodology_version ON documents(methodology_version_id);

-- Every regulatory constant, with its source. No row without version_id
-- and section_ref. Multiple rows may share the same key, differentiated
-- by applicability (e.g. several charcoal emission factors depending on
-- carbonisation losses, kiln yield, wood-to-charcoal ratio, or whether
-- the source is an IPCC default, a national value or a field measurement).
-- The system never picks one on its own. extraction_method='llm_unverified'
-- values must never be silently consumed by a calculation; extraction_method
-- ='llm_extracted' values become trusted only once verified_by/verified_at
-- are set by a human.
CREATE TABLE IF NOT EXISTS regulatory_values (
    id                 SERIAL       PRIMARY KEY,
    version_id         INTEGER      NOT NULL REFERENCES methodology_version_history(id) ON DELETE CASCADE,
    key                VARCHAR(200) NOT NULL,
    value              TEXT         NOT NULL,
    unit               VARCHAR(50),
    applicability      JSONB        NOT NULL DEFAULT '{}',
    section_ref        VARCHAR(200) NOT NULL,
    page_ref           VARCHAR(50),
    extraction_method  VARCHAR(20)  NOT NULL DEFAULT 'llm_extracted'
        CHECK (extraction_method IN ('manual', 'llm_extracted', 'llm_unverified')),
    verified_by        VARCHAR(200),
    verified_at        TIMESTAMPTZ,
    notes              TEXT,
    created_at         TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regulatory_values_version ON regulatory_values(version_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_values_key ON regulatory_values(key);

-- ============================================================
-- SPEC-03 -- Moteur de resolution de parametres (docs/SPEC-03.md)
--
-- Tranche fine : schema complet (T1-T4), moteur limite a EF_CO2/EF_nonCO2
-- charbon. Migration additive -- etend project_parameters (existant),
-- cree regulatory_value_preferences, project_parameter_alternatives et
-- project_open_questions.
-- ============================================================

ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS defendability_argument TEXT;
ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS original_proposed_value TEXT;
ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS resolution_engine_version VARCHAR(20);
ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;

-- Hierarchie de preference entre valeurs regulatory_values candidates pour
-- une meme cle, sous une condition de contexte projet donnee. N'existait pas
-- dans SPEC-01 (qui extrait des valeurs, pas des ordres de preference) --
-- ajoutee ici a la demande de l'utilisateur (01.08.2026), avec la meme
-- discipline de tracabilite que regulatory_values : une regle
-- extraction_method='llm_unverified' ne peut jamais servir a classer
-- automatiquement.
CREATE TABLE IF NOT EXISTS regulatory_value_preferences (
    id                 SERIAL       PRIMARY KEY,
    version_id         INTEGER      NOT NULL REFERENCES methodology_version_history(id) ON DELETE CASCADE,
    key                VARCHAR(200) NOT NULL,
    context_condition  JSONB        NOT NULL DEFAULT '{}',
    regulatory_value_id INTEGER     NOT NULL REFERENCES regulatory_values(id) ON DELETE CASCADE,
    rank               INTEGER      NOT NULL,
    obligation         VARCHAR(30)  NOT NULL
        CHECK (obligation IN ('mandatory', 'default_permitted', 'optional_conservative_override')),
    rationale          TEXT         NOT NULL,
    section_ref        VARCHAR(200) NOT NULL,
    page_ref           VARCHAR(50),
    extraction_method  VARCHAR(20)  NOT NULL DEFAULT 'llm_extracted'
        CHECK (extraction_method IN ('manual', 'llm_extracted', 'llm_unverified')),
    verified_by        VARCHAR(200),
    verified_at        TIMESTAMPTZ,
    created_at         TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rvp_version_key ON regulatory_value_preferences(version_id, key);

-- Une ligne par candidat pour un parametre d'un projet donne : le retenu et
-- les ecartes. `rank` est la position dans la hierarchie de preference de la
-- methodologie (regulatory_value_preferences) -- elle ne dit PAS a elle
-- seule lequel est retenu, puisqu'un fait non deductible (reponse de
-- l'utilisateur a une project_open_questions) peut faire retenir une option
-- de rang 2 ou 3. `is_selected` porte cette information explicitement ; tout
-- candidat non retenu doit avoir un motif.
CREATE TABLE IF NOT EXISTS project_parameter_alternatives (
    id                          SERIAL       PRIMARY KEY,
    project_parameter_id        INTEGER      NOT NULL REFERENCES project_parameters(id) ON DELETE CASCADE,
    value                       TEXT         NOT NULL,
    unit                        VARCHAR(50),
    regulatory_value_id         INTEGER      REFERENCES regulatory_values(id) ON DELETE SET NULL,
    external_reference_value_id INTEGER,
    section_ref                 VARCHAR(200),
    applicability                JSONB       NOT NULL DEFAULT '{}',
    rank                        INTEGER      NOT NULL,
    is_selected                 BOOLEAN      NOT NULL DEFAULT FALSE,
    rejection_reason            TEXT,
    created_at                  TIMESTAMPTZ  DEFAULT NOW(),
    CHECK (is_selected OR rejection_reason IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_ppa_project_parameter ON project_parameter_alternatives(project_parameter_id);

-- Un fait que le moteur ne peut pas deduire du contexte du projet, pose a
-- l'utilisateur plutot que suppose.
CREATE TABLE IF NOT EXISTS project_open_questions (
    id                SERIAL       PRIMARY KEY,
    project_id        INTEGER      NOT NULL REFERENCES user_projects(id) ON DELETE CASCADE,
    question_key      VARCHAR(100) NOT NULL,
    question_text     TEXT         NOT NULL,
    blocks_param_keys TEXT[]       NOT NULL DEFAULT '{}',
    status            VARCHAR(20)  NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'answered', 'not_applicable')),
    answer_value      TEXT,
    answered_by       VARCHAR(200),
    answered_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (project_id, question_key)
);

CREATE INDEX IF NOT EXISTS idx_poq_project_status ON project_open_questions(project_id, status);

-- ============================================================
-- SPEC-04 -- Generation de l'argument de defendabilite par IA (docs/SPEC-04.md)
--
-- Additive uniquement. Le gabarit structure (SPEC-03) n'est pas supprime --
-- c'est le repli systematique quand la generation IA echoue ou est rejetee
-- par le garde-fou (aucun chiffre/reference hors du fact set fourni).
-- ============================================================

ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS defendability_argument_source VARCHAR(20)
    DEFAULT 'template' CHECK (defendability_argument_source IN ('ai_generated', 'template'));
ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS defendability_argument_model VARCHAR(50);
ALTER TABLE project_parameters ADD COLUMN IF NOT EXISTS defendability_argument_generated_at TIMESTAMPTZ;
"""


def ensure_schema():
    try:
        with get_cursor(dict_cursor=False) as cur:
            cur.execute(SCHEMA_SQL)
        logger.info("Database schema verified/created successfully.")
    except Exception as e:
        logger.error("Failed to create database schema: %s", e)
        raise
