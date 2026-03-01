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
        'example_valver', 'example_other', 'rule_update', 'other'
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
    standard VARCHAR(50),
    category VARCHAR(100),
    sector VARCHAR(200),
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'under_revision', 'draft', 'withdrawn')),
    applicability TEXT,
    description TEXT,
    source_url TEXT,
    superseded_by VARCHAR(50),
    project_count INTEGER DEFAULT 0,
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

INSERT INTO standards (name, slug, description) VALUES
    ('Gold Standard', 'goldstandard', 'Gold Standard for the Global Goals - carbon credit certification'),
    ('Verra VCS', 'verra', 'Verified Carbon Standard by Verra - voluntary carbon market')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO standard_versions (standard_id, version, effective_date, status) VALUES
    ((SELECT id FROM standards WHERE slug = 'goldstandard'), '1.x', '2020-01-01', 'active'),
    ((SELECT id FROM standards WHERE slug = 'verra'), '4.4', '2023-01-01', 'active')
ON CONFLICT (standard_id, version) DO NOTHING;
"""


def ensure_schema():
    try:
        with get_cursor(dict_cursor=False) as cur:
            cur.execute(SCHEMA_SQL)
        logger.info("Database schema verified/created successfully.")
    except Exception as e:
        logger.error("Failed to create database schema: %s", e)
        raise
