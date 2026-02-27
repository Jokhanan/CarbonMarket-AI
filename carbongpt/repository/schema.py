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

CREATE INDEX IF NOT EXISTS idx_documents_standard_version ON documents(standard_version_id);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_ingestion_status ON documents(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_document_sections_document ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section_id);

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
