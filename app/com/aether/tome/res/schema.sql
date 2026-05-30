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
--   VALUE OBJECTS → columns on the owning entity's table, not a separate table
--     Metadata (name, is_active, created_at, modified_at, description?):
--     has no independent identity or lifecycle outside the Predicate that owns
--     it.  Fields dissolved directly into the predicates table, consistent
--     with how name/description are handled on NodeDevice, DeviceType,
--     NodeMesh, and every other model class.
--
-- Table inventory
--   device_types          -- DeviceType         (open-ended hardware platform)
--   devices          -- NodeDevice         (id, name, description, type→FK, is_emulated)
--   node_mesh_memberships -- NodeMeshMembership (device_id, mesh_id,
--                                                mesh_roles  INT[]  ← ordinals only,
--                                                is_admin, is_anchor, is_root,
--                                                joined_at, last_seen)
--   predicates            -- Predicate base     (id, name, is_active,
--                                                created_at, modified_at, description?,
--                                                predicate_type smallint,
--                                                predicate_family smallint)
--   predicate_geometric   -- Geometric family   (predicate_id→FK, geometry JSONB)
--   predicate_behavioral  -- Behavioral family  (future; commented out until needed)
--   predicate_ranging     -- Ranging family     (future; commented out until needed)
--   node_meshes           -- NodeMesh           (id, name, status INT ← ordinal only,
--                                                description, api_version)
--   node_mesh_predicates  -- NodeMesh↔Predicate association (ordered)
--
-- NodeMesh.nodes resolves to List[NodeMeshMembership] via node_mesh_memberships.mesh_id.
-- No separate join table is required; the membership FK is the association.
--
-- Dropped tables (replaced by Python enums or dissolved into owning entity):
--   node_mesh_roles    → NodeMeshRole   enum in code
--   node_mesh_statuses → NodeMeshStatus enum in code
--   predicate_metadata → columns dissolved into predicates table
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
--              type INT→FK, is_emulated BOOLEAN)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS devices (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    type        INT          NOT NULL REFERENCES device_types(ordinal),
    is_active BOOLEAN      NOT NULL DEFAULT TRUE,
    is_emulated BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
);

CREATE INDEX IF NOT EXISTS idx_devices_type        ON devices(type);
CREATE INDEX IF NOT EXISTS idx_devices_is_emulated ON devices(is_emulated);

-- ---------------------------------------------------------------------------
-- Users  (id UUID, username VARCHAR UNIQUE, display_name VARCHAR, created_at)
--
-- A User is a human principal who owns devices and holds admin rights in
-- meshes.  The record is created locally on first login from the external
-- identity provider.  username is the canonical handle from the IdP.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    username     VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ---------------------------------------------------------------------------
-- UserSessions  (id, user_id→users, device_id→devices,
--               created_at, expires_at, last_active_at, is_active)
--
-- Records a user's active presence on a specific device.
-- Invariants enforced here:
--   • One active session per user  (partial unique index)
--   • One active session per device (partial unique index)
-- When is_active is set to FALSE all downstream mesh memberships for this
-- session must be removed by the service layer.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
    id             UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID                     NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    device_id      UUID                     NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at     TIMESTAMP WITH TIME ZONE NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active      BOOLEAN                  NOT NULL DEFAULT TRUE
);

-- At most one active session per user and per device
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_sessions_active_user
    ON user_sessions(user_id) WHERE is_active = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_sessions_active_device
    ON user_sessions(device_id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id   ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON user_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- ---------------------------------------------------------------------------
-- NodeMeshMembership
--   device_id   UUID → devices(id)       ON DELETE CASCADE
--   mesh_id     UUID → node_meshes(id)   ON DELETE CASCADE (deferred ALTER below)
--   user_id     UUID → users(id)         ON DELETE CASCADE
--             The user whose active session authorises this membership.
--             Admin rights belong to the user, not the device.
--   session_id  UUID → user_sessions(id) ON DELETE CASCADE
--             When a session is deleted (hard remove) the membership cascades
--             away automatically.  Soft expiry (is_active=FALSE) is handled
--             by the service layer calling drop_memberships_for_session().
--   mesh_roles  INT[]  NodeMeshRole ordinals.  0=MEMBER 1=GATEWAY 2=ADMIN 3=ROOT
--   is_admin    BOOLEAN — the user has admin rights in this mesh
--   is_anchor   BOOLEAN — device has a fixed, known position
--   is_root     BOOLEAN — device is the topology entry point
--   joined_at   TIMESTAMPTZ
--   last_seen   TIMESTAMPTZ
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_mesh_memberships (
    device_id    UUID                     NOT NULL REFERENCES devices(id)       ON DELETE CASCADE,
    mesh_id      UUID                     NOT NULL,
    user_id      UUID                     NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
    session_id   UUID                     NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    mesh_roles   INT[]                    NOT NULL DEFAULT '{}',
    is_admin     BOOLEAN                  NOT NULL DEFAULT FALSE,
    is_anchor    BOOLEAN                  NOT NULL DEFAULT FALSE,
    is_root      BOOLEAN                  NOT NULL DEFAULT FALSE,
    joined_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen    TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (device_id, mesh_id)
);

CREATE INDEX IF NOT EXISTS idx_nmm_mesh_id    ON node_mesh_memberships(mesh_id);
CREATE INDEX IF NOT EXISTS idx_nmm_device_id  ON node_mesh_memberships(device_id);
CREATE INDEX IF NOT EXISTS idx_nmm_user_id    ON node_mesh_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_nmm_session_id ON node_mesh_memberships(session_id);
CREATE INDEX IF NOT EXISTS idx_nmm_is_root    ON node_mesh_memberships(is_root);
CREATE INDEX IF NOT EXISTS idx_nmm_is_admin   ON node_mesh_memberships(is_admin);

-- ---------------------------------------------------------------------------
-- Predicates — Class Table Inheritance (base + family child tables)
--
-- Metadata fields (name, is_active, created_at, modified_at, description) are
-- dissolved directly into this table.  Metadata is a Value Object — it has no
-- independent identity or lifecycle outside the Predicate that owns it.
-- Keeping it as a separate table required a JOIN on every predicate read, an
-- ownership trigger for cascade deletion, and a redundant UUID.  Dissolving it
-- is consistent with how name/description are handled on every other model
-- class (NodeDevice, DeviceType, NodeMesh).
--
-- predicate_type   smallint — Predicate.Type enum ordinal:
--   0=POINT  1=LINE_SEGMENT  2=PLANE  3=SPHERE  4=BOX
--   No CHECK constraint: new subtypes added without schema migration.
--
-- predicate_family smallint — Predicate.Family enum ordinal:
--   0=GEOMETRIC  1=BEHAVIOR  2=RANGING
--   CHECK on known family ordinals; new families require a new child table
--   anyway, so adding a CHECK value is the appropriate migration at that point.
--
-- Why JSONB geometry per family child rather than named columns per subtype:
--   - New subtype within a family → zero schema migration, new Python class only.
--   - New family → one CREATE TABLE on a new empty table (non-blocking).
--   - STI (named columns per subtype) multiplies NULLs and requires ALTER TABLE
--     ADD COLUMN on every subtype addition.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicates (
    id               UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Metadata fields (Value Object dissolved into owning entity)
    name             VARCHAR(255)             NOT NULL,
    is_active        BOOLEAN                  NOT NULL DEFAULT TRUE,
    -- created_at / modified_at are set and maintained exclusively by the DB.
    -- The application layer must not supply or override these values; the
    -- trg_set_modified_at trigger ensures modified_at is always current.
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description      TEXT,
    -- Predicate discriminators
    predicate_type   smallint                 NOT NULL,
    predicate_family smallint                 NOT NULL
        CHECK (predicate_family IN (0, 1, 2))
);

CREATE INDEX IF NOT EXISTS idx_predicates_name        ON predicates(name);
CREATE INDEX IF NOT EXISTS idx_predicates_is_active   ON predicates(is_active);
CREATE INDEX IF NOT EXISTS idx_predicates_type        ON predicates(predicate_type);
CREATE INDEX IF NOT EXISTS idx_predicates_family      ON predicates(predicate_family);

-- ---------------------------------------------------------------------------
-- Trigger: set modified_at = CURRENT_TIMESTAMP on every UPDATE.
-- The application layer is not permitted to set this value; it is owned
-- entirely by the database.  The trigger fires BEFORE UPDATE so the
-- written row always carries the authoritative modification timestamp.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_set_modified_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.modified_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_predicates_set_modified_at
BEFORE UPDATE ON predicates
FOR EACH ROW
EXECUTE FUNCTION trg_set_modified_at();

-- ---------------------------------------------------------------------------
-- predicate_geometric  (family child — Predicate.Family.GEOMETRIC = 0)
--
-- geometry JSONB stores subtype-specific spatial data opaquely.
-- The Python class interprets the keys; the DB stores them without parsing.
--
-- Point:       {"location": {"x":0,"y":0,"z":0}}
-- LineSegment: {"start":{"x":0,"y":0,"z":0}, "end":{"x":1,"y":0,"z":0}}
-- Plane:       {"point":{"x":0,"y":0,"z":0}, "normal":{"x":0,"y":0,"z":1}}
-- Sphere:      {"point":{"x":0,"y":0,"z":0}, "radius":1.5}
-- Box:         {"min_extent":{"x":0,"y":0,"z":0}, "max_extent":{"x":1,"y":1,"z":1}}
-- Cylinder:    {"point":{...}, "axis":{...}, "radius":0.5, "height":2.0}  ← no migration
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicate_geometric (
    predicate_id UUID  PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
    geometry     JSONB NOT NULL
);

-- ---------------------------------------------------------------------------
-- predicate_behavioral  (family child — Predicate.Family.BEHAVIOR = 1)
-- Placeholder: CREATE when the first behavioral predicate type is implemented.
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS predicate_behavioral (
--     predicate_id UUID  PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
--     config       JSONB NOT NULL
-- );

-- ---------------------------------------------------------------------------
-- predicate_ranging  (family child — Predicate.Family.RANGING = 2)
-- Placeholder: CREATE when the first ranging predicate type is implemented.
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS predicate_ranging (
--     predicate_id UUID  PRIMARY KEY REFERENCES predicates(id) ON DELETE CASCADE,
--     config       JSONB NOT NULL
-- );

-- ---------------------------------------------------------------------------
-- NodeMesh  (id UUID, name VARCHAR,
--            status INT — NodeMeshStatus ordinal; Python enum provides detail.
--                         0=UNKNOWN  1=MINIMAL  2=QUORUM  3=CALIBRATION
--            description TEXT, api_version VARCHAR)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_meshes (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    status      INT          NOT NULL DEFAULT 0,
    description TEXT,
    api_version VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_node_meshes_name   ON node_meshes(name);
CREATE INDEX IF NOT EXISTS idx_node_meshes_status ON node_meshes(status);

-- ---------------------------------------------------------------------------
-- node_mesh_predicates  (NodeMesh ↔ Predicate, ordered list)
-- position preserves List[Predicate] ordering from NodeMesh.predicates.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS node_mesh_predicates (
    mesh_id      UUID NOT NULL REFERENCES node_meshes(id)  ON DELETE CASCADE,
    predicate_id UUID NOT NULL REFERENCES predicates(id)   ON DELETE CASCADE,
    position     INT  NOT NULL DEFAULT 0,
    PRIMARY KEY (mesh_id, predicate_id)
);

CREATE INDEX IF NOT EXISTS idx_nmp_mesh_id ON node_mesh_predicates(mesh_id);

-- ---------------------------------------------------------------------------
-- Deferred FK: node_mesh_memberships.mesh_id → node_meshes(id)
-- node_mesh_memberships is defined before node_meshes; FK added here.
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
VALUES ('8.0.0',
        'v8: DB owns UUID generation and all timestamps; '
        'gen_random_uuid() defaults on id columns; '
        'created_at/modified_at defaults on predicates; '
        'trg_set_modified_at trigger on predicates; '
        'joined_at default on node_mesh_memberships')
ON CONFLICT DO NOTHING;

INSERT INTO schema_versions (version, description)
VALUES ('9.0.0',
        'v9: users-as-owners — introduce users and user_sessions tables; '
        'node_mesh_memberships gains user_id and session_id FK columns; '
        'admin rights transferred from device to user; '
        'partial unique indexes enforce one-active-session-per-user and per-device')
ON CONFLICT DO NOTHING;