-- ============================================================================
-- Aether / Tome Server — node_mesh_funcs.sql
-- Functions for NodeMeshMembershipRepo and MeshRepo.
--
-- NodeMeshMembership:
--   mesh_roles input is a plain INT array [0, 2, ...] (ordinals from Python
--   NodeMeshRole enum) OR an array of full role objects [{ordinal:N,...}].
--   Both forms are normalised to INT[] before storage.
--   Output is a plain INT array; Python reconstructs NodeMeshRole objects.
--
-- NodeMesh:
--   'status' in input dict is a NodeMeshStatus object {name, ordinal, ...}
--   or a plain ordinal integer; we extract the ordinal either way.
--   'nodes' contains NodeMeshMembership dicts matching NodeMesh.FIELD_TYPES.
--   'predicates' contains Predicate dicts (Metadata fields dissolved in).
-- ============================================================================

-- -------------------------------------------------------
-- Build a NodeMeshMembership JSONB.
-- mesh_roles is returned as a plain INT array [0, 2, ...].
-- The Python NodeMeshRole enum reconstructs full objects from those ordinals.
-- status is NOT part of NodeMeshMembership; it lives on NodeMesh.
-- user_id / session_id are ref-IDs; callers resolve full objects via their repos.
CREATE OR REPLACE FUNCTION _build_membership(p_device_id UUID, p_mesh_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'device_id',  m.device_id::TEXT,
        'mesh_id',    m.mesh_id::TEXT,
        'user_id',    m.user_id::TEXT,
        'session_id', m.session_id::TEXT,
        'is_admin',   m.is_admin,
        'is_anchor',  m.is_anchor,
        'is_root',    m.is_root,
        'joined_at',  to_char(m.joined_at,  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'last_seen',  CASE WHEN m.last_seen IS NOT NULL
                          THEN to_char(m.last_seen, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                          ELSE NULL END,
        -- Ordinals only; Python NodeMeshRole enum provides name/description
        'mesh_roles', COALESCE(
            (SELECT jsonb_agg(r ORDER BY r) FROM unnest(m.mesh_roles) r),
            '[]'::JSONB
        )
    )
    FROM node_mesh_memberships m
    WHERE m.device_id = p_device_id AND m.mesh_id = p_mesh_id;
$$;

-- -------------------------------------------------------
-- Build a complete NodeMesh JSONB.
-- 'status' is emitted as a plain INT (NodeMeshStatus ordinal).
-- Python NodeMeshStatus enum reconstructs the full object from that ordinal.
-- 'nodes' is a list of NodeMeshMembership objects (ordered by joined_at ASC
--   so the root anchor, as earliest member, is consistently first).
-- 'predicates' is a list of typed Predicate objects (ordered by position).
CREATE OR REPLACE FUNCTION _build_node_mesh(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',          m.id::TEXT,
        'name',        m.name,
        'description', m.description,
        'api_version', m.api_version,
        -- Ordinal only; Python NodeMeshStatus enum provides name/description
        'status',      m.status::INT
    )
    FROM node_meshes m
    WHERE m.id = p_id;
$$;

-- ============================================================================
-- NodeMeshMembershipRepo
-- Keys: [DEVICE_ID, MESH_ID]  (composite identity)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_node_mesh_memberships()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_membership(device_id, mesh_id)
    FROM   node_mesh_memberships
    ORDER  BY mesh_id, device_id;
$$;

CREATE OR REPLACE FUNCTION add_many_node_mesh_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row      JSONB;
    v_ordinals INT[];
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        -- mesh_roles may arrive as [{ordinal:N,...}] (full objects) or [N] (plain ints).
        -- Normalise both cases to an INT array of ordinals.
        SELECT COALESCE(
            ARRAY(
                SELECT CASE jsonb_typeof(elem)
                           WHEN 'object'  THEN (elem->>'ordinal')::INT
                           WHEN 'number'  THEN elem::TEXT::INT
                       END
                FROM jsonb_array_elements(v_row->'mesh_roles') elem
            ),
            '{}'::INT[]
        ) INTO v_ordinals;

        -- joined_at is owned by the DB (DEFAULT CURRENT_TIMESTAMP).
        -- Any value supplied by the caller is discarded.
        -- user_id and session_id must be supplied; the device only participates
        -- via an authenticated user with an active session.
        INSERT INTO node_mesh_memberships
               (device_id, mesh_id, user_id, session_id, mesh_roles,
                is_admin, is_anchor, is_root, last_seen)
        VALUES (
            (v_row->>'device_id')::UUID,
            (v_row->>'mesh_id')::UUID,
            (v_row->>'user_id')::UUID,
            (v_row->>'session_id')::UUID,
            v_ordinals,
            COALESCE((v_row->>'is_admin')::BOOLEAN,  FALSE),
            COALESCE((v_row->>'is_anchor')::BOOLEAN, FALSE),
            COALESCE((v_row->>'is_root')::BOOLEAN,   FALSE),
            CASE WHEN v_row->>'last_seen' IS NOT NULL
                 THEN (v_row->>'last_seen')::TIMESTAMPTZ END
        );

        RETURN NEXT _build_membership(
            (v_row->>'device_id')::UUID, (v_row->>'mesh_id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_node_mesh_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row      JSONB;
    v_ordinals INT[];
    v_cnt      INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        IF v_row->'mesh_roles' IS NOT NULL THEN
            SELECT ARRAY(
                SELECT CASE jsonb_typeof(elem)
                           WHEN 'object' THEN (elem->>'ordinal')::INT
                           WHEN 'number' THEN elem::TEXT::INT
                       END
                FROM jsonb_array_elements(v_row->'mesh_roles') elem
            ) INTO v_ordinals;
        END IF;

        UPDATE node_mesh_memberships
        SET mesh_roles = COALESCE(v_ordinals,                         mesh_roles),
            is_admin   = COALESCE((v_row->>'is_admin')::BOOLEAN,      is_admin),
            is_anchor  = COALESCE((v_row->>'is_anchor')::BOOLEAN,     is_anchor),
            is_root    = COALESCE((v_row->>'is_root')::BOOLEAN,       is_root),
            joined_at  = COALESCE((v_row->>'joined_at')::TIMESTAMPTZ, joined_at),
            last_seen  = COALESCE((v_row->>'last_seen')::TIMESTAMPTZ, last_seen)
        WHERE device_id = (v_row->>'device_id')::UUID
          AND mesh_id = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('membership (%s,%s) not found',
                                       v_row->>'device_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT _build_membership(
            (v_row->>'device_id')::UUID, (v_row->>'mesh_id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_node_mesh_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_membership(
            (v_row->>'device_id')::UUID, (v_row->>'mesh_id')::UUID);

        DELETE FROM node_mesh_memberships
        WHERE device_id = (v_row->>'device_id')::UUID
          AND mesh_id = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('membership (%s,%s) not found',
                                       v_row->>'device_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- MeshRepo
-- 'status' in the input dict is a NodeMeshStatus object {name, ordinal, ...}
-- or a plain ordinal integer; we extract the ordinal either way.
-- 'nodes' contains NodeMeshMembership dicts (not Device dicts).
-- 'predicates' contains Predicate dicts with Metadata fields dissolved in.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_node_meshes()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_node_mesh(id) FROM node_meshes ORDER BY name;
$$;

CREATE OR REPLACE FUNCTION add_many_node_meshes(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row     JSONB;
    v_mesh_id UUID;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        -- id is owned by the DB; any value in the payload is discarded.

        INSERT INTO node_meshes (name, status, description, api_version)
        VALUES (
            v_row->>'name',
            COALESCE(v_row->>'status')::INT,
            v_row->>'description',
            v_row->>'api_version'
        )
        RETURNING id INTO v_mesh_id;

        RETURN NEXT _build_node_mesh(v_mesh_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_node_meshes(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row     JSONB;
    v_mesh_id UUID;
    v_status  INT;
    v_cnt     INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_mesh_id := (v_row->>'id')::UUID;

        UPDATE node_meshes
        SET name        = COALESCE(v_row->>'name',        name),
            status      = COALESCE(COALESCE(v_row->>'status')::INT,              status),
            description = COALESCE(v_row->>'description', description),
            api_version = COALESCE(v_row->>'api_version', api_version)
        WHERE id = v_mesh_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('node_mesh id %s not found', v_mesh_id);
        END IF;
        RETURN NEXT _build_node_mesh(v_mesh_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_node_meshes(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row     JSONB;
    v_mesh_id UUID;
    v_snap    JSONB;
    v_cnt     INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_mesh_id := (v_row->>'id')::UUID;
        v_snap    := _build_node_mesh(v_mesh_id);

        -- ON DELETE CASCADE removes node_mesh_memberships + node_mesh_predicates rows
        DELETE FROM node_meshes WHERE id = v_mesh_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('node_mesh id %s not found', v_mesh_id);
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- NodeMeshPredicateMembershipRepo
-- Keys: [PREDICATE_ID, MESH_ID]  (composite identity)
-- Manages the node_mesh_predicates association table.
-- Predicates are independent resources; a predicate may belong to many meshes.
-- ============================================================================

-- Build a NodeMeshPredicateMembership JSONB from the association table.
CREATE OR REPLACE FUNCTION _build_predicate_membership(p_predicate_id UUID, p_mesh_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'predicate_id', nmp.predicate_id::TEXT,
        'mesh_id',      nmp.mesh_id::TEXT,
        'position',     nmp.position
    )
    FROM node_mesh_predicates nmp
    WHERE nmp.predicate_id = p_predicate_id AND nmp.mesh_id = p_mesh_id;
$$;

CREATE OR REPLACE FUNCTION get_all_node_mesh_predicate_memberships()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_predicate_membership(predicate_id, mesh_id)
    FROM   node_mesh_predicates
    ORDER  BY mesh_id, position;
$$;

CREATE OR REPLACE FUNCTION add_many_node_mesh_predicate_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO node_mesh_predicates (mesh_id, predicate_id, position)
        VALUES (
            (v_row->>'mesh_id')::UUID,
            (v_row->>'predicate_id')::UUID,
            COALESCE((v_row->>'position')::INT, 0)
        );
        RETURN NEXT _build_predicate_membership(
            (v_row->>'predicate_id')::UUID, (v_row->>'mesh_id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_node_mesh_predicate_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        UPDATE node_mesh_predicates
        SET    position = COALESCE((v_row->>'position')::INT, position)
        WHERE  predicate_id = (v_row->>'predicate_id')::UUID
          AND  mesh_id      = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate membership (%s,%s) not found',
                                       v_row->>'predicate_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT _build_predicate_membership(
            (v_row->>'predicate_id')::UUID, (v_row->>'mesh_id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_node_mesh_predicate_memberships(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_predicate_membership(
            (v_row->>'predicate_id')::UUID, (v_row->>'mesh_id')::UUID);

        DELETE FROM node_mesh_predicates
        WHERE  predicate_id = (v_row->>'predicate_id')::UUID
          AND  mesh_id      = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate membership (%s,%s) not found',
                                       v_row->>'predicate_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;