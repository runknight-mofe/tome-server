-- Aether Mesh Management System - PostgreSQL Schema
-- Version: 1.0.0
-- Description: Complete schema for mesh metadata, node state, predicates, and audit trail

-- ============================================================================
-- CORE MESH INFRASTRUCTURE
-- ============================================================================

-- Meshes table: Stores mesh metadata and identifying information
CREATE TABLE meshes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'archived', 'deleted', 'suspended')),
    root_node_id VARCHAR(255),  -- ID of the ROOT anchor for this mesh
    operating_mode VARCHAR(50) NOT NULL DEFAULT 'unknown'
        CHECK (operating_mode IN ('unknown', 'minimal', 'quorum', 'calibration')),
    coordinate_frame_metadata JSONB,  -- Stored frame data for recovery
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_node_id VARCHAR(255),
    UNIQUE(name)
);

-- Nodes table: Stores node membership, type, and state
CREATE TABLE nodes (
    id VARCHAR(255) NOT NULL,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL 
        CHECK (type IN ('anchor', 'client')),
    role VARCHAR(50) DEFAULT 'member'
        CHECK (role IN ('member', 'gateway', 'admin', 'root')),
    
    -- Physical state
    position_x FLOAT8,
    position_y FLOAT8,
    position_z FLOAT8,
    
    -- Quaternion orientation (for emulated devices)
    orientation_qx FLOAT8 DEFAULT 0.0,
    orientation_qy FLOAT8 DEFAULT 0.0,
    orientation_qz FLOAT8 DEFAULT 0.0,
    orientation_qw FLOAT8 DEFAULT 1.0,
    
    -- Acceleration (m/s^2) for emulated devices
    accel_x FLOAT8 DEFAULT 0.0,
    accel_y FLOAT8 DEFAULT 0.0,
    accel_z FLOAT8 DEFAULT 0.0,
    
    -- Node health & comms
    status VARCHAR(50) NOT NULL DEFAULT 'offline'
        CHECK (status IN ('online', 'offline', 'degraded', 'error')),
    signal_quality FLOAT8 DEFAULT 0.0 CHECK (signal_quality BETWEEN 0 AND 1),
    rssi FLOAT8 DEFAULT -120.0,  -- dBm
    
    -- Mesh participation
    is_admin BOOLEAN DEFAULT FALSE,
    is_root BOOLEAN DEFAULT FALSE,
    is_emulated BOOLEAN DEFAULT FALSE,  -- Mark as software-emulated device
    last_seen TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB,  -- Device-specific properties (vendor, fw version, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (mesh_id, id)
);

-- ============================================================================
-- PREDICATES & EVENT DETECTION
-- ============================================================================

-- Predicates table: Geometric shapes for event detection
CREATE TABLE predicates (
    id VARCHAR(255) NOT NULL,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL 
        CHECK (type IN ('point', 'line', 'box', 'circle', 'sphere', 'cylinder')),
    
    -- Anchor point (all predicates have a position reference)
    position_x FLOAT8 NOT NULL,
    position_y FLOAT8 NOT NULL,
    position_z FLOAT8 NOT NULL,
    
    -- Geometry-specific properties (stored as JSON for flexibility)
    -- Examples:
    -- line: {"end_x": 5.0, "end_y": 2.0, "end_z": 1.0}
    -- box: {"width": 2.0, "height": 1.5, "depth": 1.0}
    -- circle: {"radius": 0.5, "normal_x": 0, "normal_y": 0, "normal_z": 1}
    -- sphere: {"radius": 1.5}
    -- cylinder: {"radius": 0.3, "height": 2.0, "axis_x": 0, "axis_y": 0, "axis_z": 1}
    geometry JSONB NOT NULL,
    
    -- Event configuration
    hysteresis FLOAT8 DEFAULT 0.05,  -- Proximity hysteresis in meters
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Event detector reference
    event_type VARCHAR(100),  -- proximity, boundary, gesture, collision, etc.
    event_id VARCHAR(255),    -- ID of associated event detector
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_node_id VARCHAR(255),
    
    PRIMARY KEY (mesh_id, id),
    FOREIGN KEY (mesh_id, event_id) REFERENCES mesh_event_detectors(mesh_id, id) 
        ON DELETE SET NULL
);

-- Event detectors table: Manages predicate-based event rules
CREATE TABLE mesh_event_detectors (
    id VARCHAR(255) NOT NULL,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    predicate_id VARCHAR(255),
    
    -- Event rule
    event_type VARCHAR(100) NOT NULL,
    trigger_on_entry BOOLEAN DEFAULT TRUE,
    trigger_on_exit BOOLEAN DEFAULT TRUE,
    trigger_on_dwell BOOLEAN DEFAULT FALSE,
    dwell_duration_ms INTEGER DEFAULT NULL,
    
    -- Configuration
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (mesh_id, id),
    FOREIGN KEY (mesh_id, predicate_id) REFERENCES predicates(mesh_id, id) 
        ON DELETE CASCADE
);

-- ============================================================================
-- EVENTS & AUDIT TRAIL
-- ============================================================================

-- Mesh events table: Complete audit and event history
CREATE TABLE mesh_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    
    -- Event source & classification
    source VARCHAR(50) NOT NULL 
        CHECK (source IN ('user', 'runtime', 'system', 'api')),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'info'
        CHECK (severity IN ('debug', 'info', 'warn', 'error', 'critical')),
    
    -- Event participants
    predicate_id VARCHAR(255),
    node_id VARCHAR(255),
    triggered_by_node_id VARCHAR(255),  -- Which node detected/triggered
    
    -- Event details
    event_data JSONB,  -- Flexible event-specific data
    message TEXT,
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER DEFAULT NULL,  -- For events with duration (dwell, motion, etc.)
    
    -- Traceability
    request_id VARCHAR(255),  -- Correlate with API requests
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RANGING & OBSERVATION HISTORY
-- ============================================================================

-- Ranging measurements table: Historical ranging data for analysis
CREATE TABLE ranging_measurements (
    id BIGSERIAL PRIMARY KEY,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    anchor_id VARCHAR(255) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    
    distance FLOAT8 NOT NULL,
    variance FLOAT8,
    signal_quality FLOAT8,
    rssi FLOAT8,  -- dBm
    nlos BOOLEAN DEFAULT FALSE,
    
    azimuth FLOAT8,  -- Angle of Arrival (if available)
    elevation FLOAT8,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Diagnostics
    measurement_type VARCHAR(50),  -- 'uwb', 'twr', 'twound'
    cycle_id BIGINT  -- Group measurements in same ranging cycle
);

-- ============================================================================
-- AUTHENTICATION & ACCESS CONTROL
-- ============================================================================

-- Admin tokens table: API access tokens for authenticated operations
CREATE TABLE admin_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    
    token_hash VARCHAR(255) NOT NULL UNIQUE,  -- bcrypt hash
    token_type VARCHAR(50) DEFAULT 'api_key'
        CHECK (token_type IN ('api_key', 'jwt')),
    
    scope VARCHAR(255) DEFAULT 'mesh:admin'
        CHECK (scope IN ('mesh:admin', 'mesh:write', 'mesh:read')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(mesh_id, node_id)
);

-- ============================================================================
-- MESH STATE & SNAPSHOTS
-- ============================================================================

-- Mesh state snapshots: Point-in-time mesh configuration for recovery
CREATE TABLE mesh_state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    
    -- State snapshot
    nodes_json JSONB NOT NULL,          -- Complete node catalog
    predicates_json JSONB NOT NULL,     -- Complete predicate catalog
    frame_data_json JSONB,              -- Coordinate frame state
    operating_mode VARCHAR(50),
    gdop FLOAT8,
    anchor_count INTEGER,
    client_count INTEGER,
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'periodic'
        CHECK (source IN ('periodic', 'manual', 'recovery')),
    snapshot_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Keep recent snapshots for rollback capability
    created_by_node_id VARCHAR(255)
);

-- ============================================================================
-- PERFORMANCE & DIAGNOSTICS
-- ============================================================================

-- Mesh health metrics: Rolling health status snapshots
CREATE TABLE mesh_health_metrics (
    id BIGSERIAL PRIMARY KEY,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    
    -- Topology metrics
    anchor_count INTEGER,
    client_count INTEGER,
    online_node_count INTEGER,
    offline_node_count INTEGER,
    average_signal_quality FLOAT8,
    
    -- Fusion metrics
    gdop FLOAT8,
    position_residual_rms FLOAT8,
    update_frequency_hz FLOAT8,
    
    -- Events
    event_count_1min INTEGER DEFAULT 0,
    event_count_5min INTEGER DEFAULT 0,
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================================================

-- Nodes indexes
CREATE INDEX idx_nodes_mesh_id ON nodes(mesh_id);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_is_root ON nodes(is_root);
CREATE INDEX idx_nodes_joined_at ON nodes(joined_at DESC);

-- Predicates indexes
CREATE INDEX idx_predicates_mesh_id ON predicates(mesh_id);
CREATE INDEX idx_predicates_type ON predicates(type);
CREATE INDEX idx_predicates_enabled ON predicates(enabled);

-- Events indexes
CREATE INDEX idx_mesh_events_mesh_id ON mesh_events(mesh_id);
CREATE INDEX idx_mesh_events_timestamp ON mesh_events(timestamp DESC);
CREATE INDEX idx_mesh_events_type ON mesh_events(event_type);
CREATE INDEX idx_mesh_events_node_id ON mesh_events(node_id);
CREATE INDEX idx_mesh_events_predicate_id ON mesh_events(predicate_id);
CREATE INDEX idx_mesh_events_request_id ON mesh_events(request_id);

-- Ranging measurements indexes
CREATE INDEX idx_ranging_mesh_id ON ranging_measurements(mesh_id);
CREATE INDEX idx_ranging_timestamp ON ranging_measurements(timestamp DESC);
CREATE INDEX idx_ranging_cycle_id ON ranging_measurements(cycle_id);

-- Token indexes
CREATE INDEX idx_admin_tokens_mesh_id ON admin_tokens(mesh_id);
CREATE INDEX idx_admin_tokens_active ON admin_tokens(is_active) WHERE is_active = TRUE;

-- Health metrics indexes
CREATE INDEX idx_health_mesh_id ON mesh_health_metrics(mesh_id);
CREATE INDEX idx_health_timestamp ON mesh_health_metrics(timestamp DESC);

-- Snapshots indexes
CREATE INDEX idx_snapshots_mesh_id ON mesh_state_snapshots(mesh_id);
CREATE INDEX idx_snapshots_created_at ON mesh_state_snapshots(created_at DESC);

-- ============================================================================
-- CONSTRAINTS & REFERENTIAL INTEGRITY
-- ============================================================================

-- Foreign key constraints
ALTER TABLE nodes
    ADD CONSTRAINT fk_nodes_mesh_id 
    FOREIGN KEY (mesh_id) REFERENCES meshes(id) ON DELETE CASCADE;

ALTER TABLE predicates
    ADD CONSTRAINT fk_predicates_mesh_id 
    FOREIGN KEY (mesh_id) REFERENCES meshes(id) ON DELETE CASCADE;

-- Ensure mesh_event_detectors references valid predicates
ALTER TABLE mesh_event_detectors
    ADD CONSTRAINT fk_events_predicate 
    FOREIGN KEY (mesh_id, predicate_id) REFERENCES predicates(mesh_id, id) 
    ON DELETE CASCADE;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Mesh topology view: Quick access to mesh state
CREATE VIEW v_mesh_topology AS
SELECT 
    m.id,
    m.name,
    m.status,
    m.operating_mode,
    COUNT(DISTINCT CASE WHEN n.type = 'anchor' THEN n.id END) as anchor_count,
    COUNT(DISTINCT CASE WHEN n.type = 'client' THEN n.id END) as client_count,
    COUNT(DISTINCT CASE WHEN n.status = 'online' THEN n.id END) as online_count,
    COUNT(DISTINCT CASE WHEN n.status = 'offline' THEN n.id END) as offline_count,
    AVG(n.signal_quality) as avg_signal_quality,
    MAX(n.updated_at) as last_update,
    COUNT(DISTINCT p.id) as predicate_count
FROM meshes m
LEFT JOIN nodes n ON m.id = n.mesh_id
LEFT JOIN predicates p ON m.id = p.mesh_id
GROUP BY m.id, m.name, m.status, m.operating_mode;

-- Node status view: Current node state summary
CREATE VIEW v_node_status AS
SELECT 
    mesh_id,
    id,
    type,
    status,
    signal_quality,
    position_x,
    position_y,
    position_z,
    is_root,
    is_admin,
    is_emulated,
    last_seen,
    joined_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_seen)) as seconds_since_seen
FROM nodes;

-- Event timeline view: Recent events with context
CREATE VIEW v_recent_events AS
SELECT 
    me.id,
    me.mesh_id,
    me.timestamp,
    me.event_type,
    me.severity,
    me.message,
    me.node_id,
    me.predicate_id,
    n.type as node_type,
    p.type as predicate_type,
    me.event_data,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - me.timestamp)) as seconds_ago
FROM mesh_events me
LEFT JOIN nodes n ON me.mesh_id = n.mesh_id AND me.node_id = n.id
LEFT JOIN predicates p ON me.mesh_id = p.mesh_id AND me.predicate_id = p.id
ORDER BY me.timestamp DESC;

-- ============================================================================
-- MIGRATION & VERSION TRACKING
-- ============================================================================

CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Record initial schema version
INSERT INTO schema_versions (version, description) VALUES 
    ('1.0.0', 'Initial Aether Mesh Management schema');

-- ============================================================================
-- GRANTS & PERMISSIONS (adjust user names as needed)
-- ============================================================================

-- Assuming you have these database roles:
-- - aether_app: Application service account
-- - aether_readonly: Read-only reporting account
-- - aether_admin: Schema management (your deploy user)

-- GRANT ALL PRIVILEGES ON DATABASE aether_mesh TO aether_app;
-- GRANT CONNECT ON DATABASE aether_mesh TO aether_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO aether_readonly;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
