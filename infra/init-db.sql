-- Voice AI Agent Database Schema
-- Production-grade schema for memory management, security, and audit logging

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =============================================================================
-- USER MANAGEMENT
-- =============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- =============================================================================
-- SHORT-TERM MEMORY (PostgreSQL backup, Redis is primary store)
-- =============================================================================

CREATE TABLE session_context (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_expires ON session_context(session_id, expires_at);
CREATE INDEX idx_session_user ON session_context(user_id, created_at DESC);

-- Auto-delete expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM session_context WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- LONG-TERM MEMORY: USER PREFERENCES
-- =============================================================================

CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,  -- 'voice', 'privacy', 'behavior', 'ui'
    key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);

CREATE INDEX idx_user_prefs_category ON user_preferences(user_id, category);

-- Trigger to update timestamp on modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_preferences_updated_at
BEFORE UPDATE ON user_preferences
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- LONG-TERM MEMORY: LEARNED BEHAVIORS
-- =============================================================================

CREATE TABLE learned_behaviors (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    behavior_type VARCHAR(50) NOT NULL,  -- 'command_shortcut', 'tool_preference', 'speech_pattern'
    pattern VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    occurrence_count INT DEFAULT 1,
    last_seen TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_behaviors ON learned_behaviors(user_id, behavior_type);
CREATE INDEX idx_behavior_pattern ON learned_behaviors USING gin(pattern gin_trgm_ops);
CREATE INDEX idx_behavior_confidence ON learned_behaviors(user_id, confidence DESC);

-- =============================================================================
-- EPISODIC MEMORY: EVENT HISTORY
-- =============================================================================

CREATE TABLE episodic_events (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- 'command', 'task', 'conversation', 'correction'
    summary TEXT NOT NULL,
    details JSONB DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_events ON episodic_events(user_id, occurred_at DESC);
CREATE INDEX idx_event_type ON episodic_events(user_id, event_type, occurred_at DESC);

-- Partition table by month for scalability (optional for future)
-- CREATE TABLE episodic_events_2026_01 PARTITION OF episodic_events
-- FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- =============================================================================
-- EPISODIC MEMORY: WEEKLY SUMMARIES
-- =============================================================================

CREATE TABLE episodic_summaries (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    summary TEXT NOT NULL,
    event_count INT NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, week_start)
);

CREATE INDEX idx_episodic_summaries ON episodic_summaries(user_id, week_start DESC);

-- Function to generate weekly summary
CREATE OR REPLACE FUNCTION generate_weekly_summary(p_user_id UUID, p_week_start DATE)
RETURNS void AS $$
DECLARE
    v_summary TEXT;
    v_count INT;
BEGIN
    SELECT
        string_agg(summary, E'\n' ORDER BY occurred_at),
        COUNT(*)
    INTO v_summary, v_count
    FROM episodic_events
    WHERE user_id = p_user_id
      AND occurred_at >= p_week_start
      AND occurred_at < p_week_start + INTERVAL '7 days';

    INSERT INTO episodic_summaries (user_id, week_start, summary, event_count)
    VALUES (p_user_id, p_week_start, COALESCE(v_summary, 'No events'), v_count)
    ON CONFLICT (user_id, week_start) DO UPDATE
    SET summary = EXCLUDED.summary,
        event_count = EXCLUDED.event_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SECURITY: AUDIT LOG
-- =============================================================================

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID,
    action VARCHAR(100) NOT NULL,  -- 'tool_execute', 'memory_access', 'permission_change'
    tool_name VARCHAR(100),
    parameters JSONB DEFAULT '{}'::JSONB,
    result VARCHAR(20) NOT NULL,  -- 'success', 'failure', 'denied', 'timeout'
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user_time ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);
CREATE INDEX idx_audit_result ON audit_log(result, created_at DESC);

-- Partition audit_log by month for better performance
-- CREATE TABLE audit_log_2026_01 PARTITION OF audit_log
-- FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- =============================================================================
-- SECURITY: PERMISSION MATRIX
-- =============================================================================

CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('read', 'write', 'execute', 'admin')),
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),  -- Admin who granted permission
    revoked_at TIMESTAMP,
    UNIQUE(user_id, tool_name)
);

CREATE INDEX idx_user_permissions ON user_permissions(user_id, tool_name) WHERE revoked_at IS NULL;

-- =============================================================================
-- SECURITY: RATE LIMITING
-- =============================================================================

CREATE TABLE rate_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    request_count INT DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW(),
    window_duration_seconds INT DEFAULT 3600,  -- 1 hour default
    max_requests INT DEFAULT 100,
    UNIQUE(user_id, tool_name, window_start)
);

CREATE INDEX idx_rate_limits ON rate_limits(user_id, tool_name, window_start);

-- Function to check and increment rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_user_id UUID,
    p_tool_name VARCHAR,
    p_max_requests INT DEFAULT 100,
    p_window_seconds INT DEFAULT 3600
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_count INT;
    v_window_start TIMESTAMP;
BEGIN
    v_window_start := DATE_TRUNC('hour', NOW());

    INSERT INTO rate_limits (user_id, tool_name, request_count, window_start, max_requests, window_duration_seconds)
    VALUES (p_user_id, p_tool_name, 1, v_window_start, p_max_requests, p_window_seconds)
    ON CONFLICT (user_id, tool_name, window_start) DO UPDATE
    SET request_count = rate_limits.request_count + 1
    RETURNING request_count INTO v_current_count;

    RETURN v_current_count <= p_max_requests;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VECTOR EMBEDDINGS (for semantic search - used with FAISS externally)
-- =============================================================================

CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,  -- 'conversation', 'command', 'document'
    content_text TEXT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,  -- 'text-embedding-ada-002', 'all-MiniLM-L6-v2'
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vector_user_type ON vector_embeddings(user_id, content_type);
CREATE INDEX idx_vector_created ON vector_embeddings(created_at DESC);

-- Note: Actual vector similarity search is handled by FAISS/Chroma
-- This table stores metadata and references to vector indices

-- =============================================================================
-- SYSTEM CONFIGURATION
-- =============================================================================

CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- Default configuration
INSERT INTO system_config (key, value, description) VALUES
    ('learning_enabled', 'true', 'Global toggle for user behavior learning'),
    ('max_session_duration_hours', '24', 'Maximum session duration before expiration'),
    ('episodic_retention_days', '90', 'Days to retain episodic events before archival'),
    ('default_rate_limit', '100', 'Default rate limit per tool per hour'),
    ('require_confirmation_threshold', '0.8', 'Confidence threshold requiring user confirmation');

-- =============================================================================
-- MAINTENANCE FUNCTIONS
-- =============================================================================

-- Cleanup old episodic events (run weekly via cron)
CREATE OR REPLACE FUNCTION archive_old_episodic_events()
RETURNS void AS $$
DECLARE
    v_retention_days INT;
BEGIN
    SELECT (value::TEXT)::INT INTO v_retention_days
    FROM system_config WHERE key = 'episodic_retention_days';

    DELETE FROM episodic_events
    WHERE occurred_at < NOW() - (v_retention_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Update user timestamp trigger
CREATE TRIGGER trigger_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create system user for automated operations
INSERT INTO users (id, email, is_active, metadata)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system@voice-ai-agent.local',
    TRUE,
    '{"role": "system", "description": "System user for automated operations"}'::JSONB
);

-- Grant statement for application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- User memory summary view
CREATE OR REPLACE VIEW user_memory_summary AS
SELECT
    u.id AS user_id,
    u.email,
    COUNT(DISTINCT up.id) AS preference_count,
    COUNT(DISTINCT lb.id) AS learned_behavior_count,
    COUNT(DISTINCT ee.id) AS episodic_event_count,
    MAX(ee.occurred_at) AS last_activity,
    u.created_at AS user_since
FROM users u
LEFT JOIN user_preferences up ON u.id = up.user_id
LEFT JOIN learned_behaviors lb ON u.id = lb.user_id
LEFT JOIN episodic_events ee ON u.id = ee.user_id
GROUP BY u.id, u.email, u.created_at;

-- Recent audit activity view
CREATE OR REPLACE VIEW recent_audit_activity AS
SELECT
    al.id,
    u.email,
    al.action,
    al.tool_name,
    al.result,
    al.created_at
FROM audit_log al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.created_at > NOW() - INTERVAL '7 days'
ORDER BY al.created_at DESC;

-- =============================================================================
-- COMPLETION
-- =============================================================================

-- Log schema initialization
DO $$
BEGIN
    RAISE NOTICE 'Voice AI Agent database schema initialized successfully';
    RAISE NOTICE 'Tables created: users, session_context, user_preferences, learned_behaviors, episodic_events, episodic_summaries, audit_log, user_permissions, rate_limits, vector_embeddings, system_config';
    RAISE NOTICE 'Functions created: cleanup_expired_sessions, generate_weekly_summary, check_rate_limit, archive_old_episodic_events';
    RAISE NOTICE 'Views created: user_memory_summary, recent_audit_activity';
END $$;
