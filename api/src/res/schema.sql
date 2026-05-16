-- ============================================================================
-- Aether / Tome Server — PostgreSQL Schema
--
-- Design principles applied here:
--
--   OPEN-ENDED sets → DB table
--     DeviceType: physical hardware platforms are operator-defined and
--     unbounded. New hardware is fielded without a code release.
--
--   CLOSED, STATIC sets → Python enum; only ordinal stored in DB
--     NodeMeshRole   (MEMBER, GATEWAY, ADMIN, ROOT): defined by the
--       application domain. A new role requires a code change to the MOFE
--       runtime that interprets it — it will never be added through the UI.
--     NodeMeshStatus (UNKNOWN, MINIMAL, QUORUM, CALIBRATION): maps 1-to-1
--       with the MOFE state machine. New states only arrive with a firmware
--       release. No DB table; ordinal stored as INT in node_meshes.status.
--
-- Table inventory
--   device_types          -- DeviceType         (open-ended hardware platform)
--   node_devices          -- NodeDevice         (id, name, description, type→FK, is_emulated)
--   node_mesh_memberships -- NodeMeshMembership (node_id, mesh_id,
--                                                mesh_roles  INT[]  <- ordinals only,
--                                                is_admin, is_anchor, is_root,
--                                                joined_at, last_seen)
--   predicate_metadata    -- Metadata           (id, name, is_active,
--                                                created_at, modified_at, description?)
--   predicates            -- Predicate base    (id, predicate_type, predicate_family, metadata_id->FK)
--   predicate_geometric   -- Geometric family  (predicate_id->FK, geometry JSONB)
--   predicate_behavioral  -- Behavioral family (future; commented out until needed)
--   predicate_ranging     -- Ranging family    (future; commented out until needed)
--   node_meshes           -- NodeMesh           (id, name, status INT <- ordinal only,
--                                                description, api_version)
--   node_mesh_devices     -- NodeMesh<->NodeDevice association (ordered)
--   node_mesh_predicates  -- NodeMesh<->Predicate association  (ordered)
--
-- Dropped tables (replaced by Python enums):
--   node_mesh_roles    -> NodeMeshRole   enum in code
--   node_mesh_statuses -> NodeMeshStatus enum in code
-- ============================================================================

-- ---------------------------------------------------------------------------
-- DeviceType  (ordinal INT, name VARCHAR, description TEXT,
--              manufacturer VARCHAR, ranging_method INT,
--              supports_aoa BOOLEAN, max_update_rate_hz FLOAT8,
--              typical_accuracy_m FLOAT8)
--
-- Represents a physical hardware platform, not a topology role.
-- The topology role (anchor vs client) lives on NodeMeshMembership.is_anchor.
--
-- ranging_method stores the RangingMethod enum ordinal (Python enum in code):
--   0  TWR       Two-Way Ranging       (each node drives the exchange)
--   1  TDOA      Time Difference of Arrival (infrastructure-side calculation)
--   2  TWR_TDOA  Hardware supports both modes; mode selected at runtime
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS device_types (
    ordinal            INT          PRIMARY KEY,
    name               VARCHAR(255) NOT NULL UNIQUE,
    description        TEXT,
    manufacturer       VARCHAR(255),
    ranging_method     INT          NOT NULL DEFAULT 0,
    supports_aoa       BOOLEAN      NOT NULL DEFAULT FALSE,
    max_update_rate_hz FLOAT8,
    typical_accuracy_m FLOAT8
);

-- ---------------------------------------------------------------------------
-- NodeDevice  (id UUID, name VARCHAR, description TEXT,
--              type DeviceType, is_emulated BOOLEAN)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_devices (
    id          UUID         PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    type        INT          NOT NULL REFERENCES device_types(ordinal),
    is_emulated BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_node_devices_type        ON node_devices(type);
CREATE INDEX IF NOT EXISTS idx_node_devices_is_emulated ON node_devices(is_emulated);

-- ---------------------------------------------------------------------------
-- NodeMeshMembership
--   node_id    UUID
--   mesh_id    UUID
--   mesh_roles INT[]     NodeMeshRole ordinals only.  The Python enum
--                        provides name/description; no DB table needed.
--                        0=MEMBER  1=GATEWAY  2=ADMIN  3=ROOT
--   is_admin   BOOLEAN
--   is_anchor  BOOLEAN   TRUE=anchor (fixed, known position)
--                        FALSE=client/tag (mobile, unknown position)
--                        Topology role relocated from DeviceType.
--   is_root    BOOLEAN
--   joined_at  TIMESTAMPTZ
--   last_seen  TIMESTAMPTZ
--
-- mesh_id FK added via ALTER after node_meshes is defined below.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_mesh_memberships (
    node_id    UUID                     NOT NULL,
    mesh_id    UUID                     NOT NULL,
    mesh_roles INT[]                    NOT NULL DEFAULT '{}',
    is_admin   BOOLEAN                  NOT NULL DEFAULT FALSE,
    is_anchor  BOOLEAN                  NOT NULL DEFAULT FALSE,
    is_root    BOOLEAN                  NOT NULL DEFAULT FALSE,
    joined_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen  TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (node_id, mesh_id)
);

CREATE INDEX IF NOT EXISTS idx_nmm_mesh_id  ON node_mesh_memberships(mesh_id);
CREATE INDEX IF NOT EXISTS idx_nmm_node_id  ON node_mesh_memberships(node_id);
CREATE INDEX IF NOT EXISTS idx_nmm_is_root  ON node_mesh_memberships(is_root);
CREATE INDEX IF NOT EXISTS idx_nmm_is_admin ON node_mesh_memberships(is_admin);

-- ---------------------------------------------------------------------------
-- Metadata  (id UUID, name VARCHAR, is_active BOOLEAN,
--            created_at TIMESTAMPTZ, modified_at TIMESTAMPTZ,
--            description TEXT  [OPTIONAL_FIELDS])
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicate_metadata (
    id          UUID                     PRIMARY KEY,
    name        VARCHAR(255)             NOT NULL,
    is_active   BOOLEAN                  NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_pred_meta_name      ON predicate_metadata(name);
CREATE INDEX IF NOT EXISTS idx_pred_meta_is_active ON predicate_metadata(is_active);

-- ---------------------------------------------------------------------------
-- Predicates — Class Table Inheritance (base + family child tables)
--
-- Pattern: one base table for identity and shared fields; one child table
-- per predicate FAMILY (not per subtype) storing geometry as JSONB.
--
-- Why JSONB geometry per family rather than named columns per subtype:
--   - Adding a new subtype within a family (e.g. Cylinder under geometric)
--     requires zero schema migration — only a new Python class.
--   - Adding a new family (e.g. behavioral, ranging) requires one new child
--     table (CREATE TABLE — non-blocking, no data touched).
--   - The alternative (named columns per subtype, STI) multiplies nullable
--     columns on every row and locks the table on every ALTER TABLE ADD COLUMN.
--   - Python from_dict() already handles JSONB->typed-object via
--     DataModelServices.deserialize_value; no extra deserialisation cost.
--
-- Current families:
--   GEOMETRIC(0)   — spatial predicates (Point, LineSegment, Plane, Sphere, Box)
--   BEHAVIORAL(1)  — future: GesturePattern, DwellZone, MotionPath
--   RANGING(2)     — future: RangingThreshold, SignalQualityFilter
--
-- Adding a new geometric subtype (e.g. Cylinder):
--   1. Write the Python class.
--   2. Register its type string in the PREDICATE_FAMILY map (Python const).
--   3. Zero SQL changes.
--
-- Adding a new family (e.g. BEHAVIORAL):
--   1. Write the Python class(es).
--   2. Add the family string to PREDICATE_FAMILY map.
--   3. CREATE TABLE predicate_behavioral (...) — one safe DDL statement.
-- ---------------------------------------------------------------------------

-- Base table: identity, discriminator, metadata FK.
-- predicate_type is a smallint — an ordinal bound to the Predicate.Type
-- enumeration defined in the data model
CREATE TABLE IF NOT EXISTS predicates (
    id             UUID         PRIMARY KEY,
    predicate_type smallint  NOT NULL,
    predicate_family smallint NOT NULL
        CHECK (predicate_family IN (0, 1, 2)),
    metadata_id    UUID         NOT NULL REFERENCES predicate_metadata(id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_predicates_type        ON predicates(predicate_type);
CREATE INDEX IF NOT EXISTS idx_predicates_family      ON predicates(predicate_family);
CREATE INDEX IF NOT EXISTS idx_predicates_metadata_id ON predicates(metadata_id);

-- ---------------------------------------------------------------------------
-- predicate_geometric  (family child for all spatial predicate subtypes)
--
-- geometry JSONB stores the subtype-specific spatial data.
-- The Python class determines how to interpret it; the DB stores it opaquely.
--
-- Point:       {"location": {"x":0,"y":0,"z":0}}
-- LineSegment: {"start":{"x":0,"y":0,"z":0}, "end":{"x":1,"y":0,"z":0}}
-- Plane:       {"point":{"x":0,"y":0,"z":0}, "normal":{"x":0,"y":0,"z":1}}
-- Sphere:      {"point":{"x":0,"y":0,"z":0}, "radius":1.5}
-- Box:         {"min_extent":{"x":0,"y":0,"z":0}, "max_extent":{"x":1,"y":1,"z":1}}
-- Cylinder:    {"point":{"x":0,"y":0,"z":0}, "axis":{"x":0,"y":0,"z":1},
--               "radius":0.5, "height":2.0}   <- no migration required
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicate_geometric (
    predicate_id UUID PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
    geometry     JSONB NOT NULL
);

-- ---------------------------------------------------------------------------
-- predicate_behavioral  (family child — future non-geometric predicates)
-- Placeholder: CREATE when the first behavioral predicate type is implemented.
-- config JSONB stores the subtype-specific detection parameters.
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS predicate_behavioral (
--     predicate_id UUID PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
--     config       JSONB NOT NULL
-- );

-- ---------------------------------------------------------------------------
-- predicate_ranging  (family child — future ranging / signal predicates)
-- Placeholder: CREATE when the first ranging predicate type is implemented.
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS predicate_ranging (
--     predicate_id UUID PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
--     config       JSONB NOT NULL
-- );

-- ---------------------------------------------------------------------------
-- NodeMesh  (id UUID, name VARCHAR,
--            status INT   NodeMeshStatus ordinal only.  The Python enum
--                         provides name/description; no DB table needed.
--                         0=UNKNOWN  1=MINIMAL  2=QUORUM  3=CALIBRATION
--            description TEXT, api_version VARCHAR)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_meshes (
    id          UUID         PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    status      INT          NOT NULL DEFAULT 0,
    description TEXT,
    api_version VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_node_meshes_name   ON node_meshes(name);
CREATE INDEX IF NOT EXISTS idx_node_meshes_status ON node_meshes(status);

-- ---------------------------------------------------------------------------
-- node_mesh_devices  (NodeMesh <-> NodeDevice, ordered list)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_mesh_devices (
    mesh_id   UUID NOT NULL REFERENCES node_meshes(id)  ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES node_devices(id) ON DELETE CASCADE,
    position  INT  NOT NULL DEFAULT 0,
    PRIMARY KEY (mesh_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_nmd_mesh_id ON node_mesh_devices(mesh_id);

-- ---------------------------------------------------------------------------
-- node_mesh_predicates  (NodeMesh <-> Predicate, ordered list)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_mesh_predicates (
    mesh_id      UUID NOT NULL REFERENCES node_meshes(id)  ON DELETE CASCADE,
    predicate_id UUID NOT NULL REFERENCES predicates(id)   ON DELETE CASCADE,
    position     INT  NOT NULL DEFAULT 0,
    PRIMARY KEY (mesh_id, predicate_id)
);

CREATE INDEX IF NOT EXISTS idx_nmp_mesh_id ON node_mesh_predicates(mesh_id);

-- ---------------------------------------------------------------------------
-- Deferred FK: node_mesh_memberships.mesh_id -> node_meshes(id)
-- ---------------------------------------------------------------------------
ALTER TABLE node_mesh_memberships
    ADD CONSTRAINT fk_nmm_mesh_id
    FOREIGN KEY (mesh_id) REFERENCES node_meshes(id) ON DELETE CASCADE;

-- ---------------------------------------------------------------------------
-- Schema version
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_versions (
    version     VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT INTO schema_versions (version, description)
VALUES ('1.0.0',
        'DeviceType is physical hardware platform; NodeMeshRole/Status are Python enums; ANCHOR/CLIENT topology role on NodeMeshMembership.is_anchor; predicate CTI+JSONB family pattern')
ON CONFLICT DO NOTHING;