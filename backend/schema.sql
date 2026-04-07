-- Reporting API POC
-- Intelligence platform: primary/secondary source fallback

CREATE TABLE IF NOT EXISTS intelligence_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- 'primary', 'secondary', 'fallback'
    priority INTEGER NOT NULL DEFAULT 0, -- lower = higher priority
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_checked_at TIMESTAMP,
    last_success_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source_id UUID REFERENCES intelligence_sources(id),
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, archived, draft, escalated
    priority INTEGER NOT NULL DEFAULT 0, -- 0=low, 1=medium, 2=high, 3=critical
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1.00), -- 0.00 to 1.00
    tags TEXT[], -- array of string tags
    metadata JSONB, -- flexible metadata
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_priority ON reports(priority);
CREATE INDEX idx_reports_source ON reports(source_id);
CREATE INDEX idx_reports_published ON reports(published_at DESC);
CREATE INDEX idx_reports_tags ON reports USING GIN(tags);

-- Insert sample sources
INSERT INTO intelligence_sources (name, type, priority) VALUES
    ('SIGINT - Primary', 'primary', 1),
    ('OSINT - Secondary', 'secondary', 2),
    ('HUMINT - Fallback', 'fallback', 3)
ON CONFLICT (name) DO NOTHING;

-- Insert sample reports
INSERT INTO reports (title, content, source_id, status, priority, confidence, tags, metadata, published_at)
SELECT 
    'Intelligence Report: ' || s.name || ' Report #' || g,
    'Detailed content for ' || s.name || ' report #' || g || '. This contains classified intelligence data with specific findings and recommendations.',
    s.id,
    CASE WHEN random() > 0.3 THEN 'active' ELSE 'archived' END,
    floor(random() * 4)::int,
    round(random()::numeric, 2),
    ARRAY['intel', s.type, 'classified'],
    jsonb_build_object('region', 'APAC', 'classification', 'SECRET', 'case_id', 'INT-' || g),
    NOW() - (random() * interval '30 days')
FROM intelligence_sources s
CROSS JOIN generate_series(1, 15) g;