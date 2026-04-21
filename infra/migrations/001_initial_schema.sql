-- ============================================================
-- Migration 001: Initial schema for AI Byggesøknad
-- ============================================================

-- Addresses
CREATE TABLE IF NOT EXISTS addresses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_text    TEXT NOT NULL,
    municipality    TEXT NOT NULL,
    municipality_no TEXT,
    postal_code     TEXT,
    postal_place    TEXT,
    lat             DOUBLE PRECISION NOT NULL,
    lng             DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326),
    raw_data        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_addresses_geom ON addresses USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_addresses_text ON addresses USING GIN(to_tsvector('norwegian', address_text));

-- Properties (Eiendommer / Matrikkel)
CREATE TABLE IF NOT EXISTS properties (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_id          UUID REFERENCES addresses(id),
    municipality_no     TEXT NOT NULL,
    municipality        TEXT NOT NULL,
    gnr                 INTEGER NOT NULL,
    bnr                 INTEGER NOT NULL,
    fnr                 INTEGER,
    snr                 INTEGER,
    areal               DOUBLE PRECISION,
    building_status     TEXT,
    geometry            GEOMETRY(MultiPolygon, 4326),
    raw_data            JSONB,
    cached_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_properties_geom ON properties USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_properties_gnr_bnr ON properties(municipality_no, gnr, bnr);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_id              UUID REFERENCES addresses(id),
    property_id             UUID REFERENCES properties(id),
    address_text            TEXT NOT NULL,
    lat                     DOUBLE PRECISION NOT NULL,
    lng                     DOUBLE PRECISION NOT NULL,
    intent_text             TEXT NOT NULL,
    classified_measure_type TEXT,
    classification_confidence DOUBLE PRECISION,
    status                  TEXT NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft','analyzing','analyzed','preparing','ready','submitted')),
    risk_level              TEXT CHECK (risk_level IN ('lav','middels','høy','ukjent')),
    application_required    BOOLEAN,
    readiness_score         INTEGER,
    ai_summary              TEXT,
    next_steps              JSONB DEFAULT '[]',
    document_requirements   JSONB DEFAULT '[]',
    warnings                JSONB DEFAULT '[]',
    analyzed_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);

-- Plan layer results (reguleringsplan, kommuneplan)
CREATE TABLE IF NOT EXISTS plan_layer_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    plan_id             TEXT,
    plan_name           TEXT,
    plan_status         TEXT NOT NULL DEFAULT 'ukjent',
    areal_formal        TEXT NOT NULL DEFAULT 'ukjent',
    hensynssoner        JSONB DEFAULT '[]',
    byggegrense         DOUBLE PRECISION,
    utnyttelsesgrad     TEXT,
    plan_url            TEXT,
    geometry            GEOMETRY(MultiPolygon, 4326),
    raw_data            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plan_results_project ON plan_layer_results(project_id);

-- Hazard results (NVE flom/skred)
CREATE TABLE IF NOT EXISTS hazard_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    flom_fare       TEXT NOT NULL DEFAULT 'ukjent',
    skred_fare      TEXT NOT NULL DEFAULT 'ukjent',
    flom_sone_id    TEXT,
    skred_sone_id   TEXT,
    notes           TEXT,
    raw_data        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hazard_results_project ON hazard_results(project_id);

-- Rules (deklarative regeldefinisjoner)
CREATE TABLE IF NOT EXISTS rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    description     TEXT,
    rule_group      TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warn'
                    CHECK (severity IN ('info','warn','fail')),
    measure_types   JSONB DEFAULT '[]',  -- which measure types this rule applies to
    logic           JSONB NOT NULL,      -- declarative rule logic
    explanation_template TEXT,
    source_refs     JSONB DEFAULT '[]',  -- e.g. ["PBL § 20-1", "TEK17 § 12-2"]
    is_blocking     BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rules_code ON rules(code);
CREATE INDEX IF NOT EXISTS idx_rules_group ON rules(rule_group);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(is_active);

-- Rule evaluation results
CREATE TABLE IF NOT EXISTS rule_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    rule_id         UUID REFERENCES rules(id),
    rule_code       TEXT NOT NULL,
    rule_name       TEXT NOT NULL,
    rule_group      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'unknown'
                    CHECK (status IN ('pass','warn','fail','unknown')),
    explanation     TEXT,
    evidence_refs   JSONB DEFAULT '[]',
    is_blocking     BOOLEAN NOT NULL DEFAULT FALSE,
    source_version  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_results_project ON rule_results(project_id);
CREATE INDEX IF NOT EXISTS idx_rule_results_status ON rule_results(status);

-- Files
CREATE TABLE IF NOT EXISTS files (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_type           TEXT NOT NULL,  -- 'pdf', 'image', 'drawing', 'report'
    original_name       TEXT,
    storage_url         TEXT NOT NULL,
    mime_type           TEXT,
    size_bytes          INTEGER,
    extracted_text      TEXT,
    parsed_geometry     JSONB,
    ai_summary          TEXT,
    validation_status   TEXT DEFAULT 'received'
                        CHECK (validation_status IN ('received','analyzing','analyzed','missing_data','flagged','approved')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);

-- Document artifacts (generated documents)
CREATE TABLE IF NOT EXISTS document_artifacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    doc_type        TEXT NOT NULL,  -- 'forhåndsvurdering', 'tiltaksbeskrivelse', 'nabovarsel', etc.
    title           TEXT NOT NULL,
    storage_url     TEXT,
    content_text    TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    ai_generated    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doc_artifacts_project ON document_artifacts(project_id);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id  UUID REFERENCES projects(id),
    event_type  TEXT NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_events(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);

-- Trigger: update updated_at on projects
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rules_updated_at
    BEFORE UPDATE ON rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
