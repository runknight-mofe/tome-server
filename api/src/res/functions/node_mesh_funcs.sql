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
CREATE OR REPLACE FUNCTION _build_membership(p_node_id UUID, p_mesh_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'node_id',    m.node_id::TEXT,
        'mesh_id',    m.mesh_id::TEXT,
        'is_admin',   m.is_admin,
        'is_anchor',  m.is_anchor,
        'is_root',    m.is_root,
        'joined_at',  to_char(m.joined_at,  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'last_seen',  CASE WHEN m.last_seen IS NOT NULL
                          THEN to_char(m.last_seen, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                          ELSE NULL END,
        -- Ordinals only; Python NodeMeshRole enum provides name/description
        'mesh_roles', COALESCE(
            (SELECT jsonb_agg(r ORDER BY r) FILTER (WHERE r IS NOT NULL) FROM unnest(m.mesh_roles) r),
            '[]'::JSONB
        )
    )
    FROM node_mesh_memberships m
    WHERE m.node_id = p_node_id AND m.mesh_id = p_mesh_id;
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
        'status',      m.status,
        -- NodeMesh.nodes is List[NodeMeshMembership], not List[NodeDevice].
        -- Membership carries the topology context the fusion engine needs:
        -- is_anchor, is_root, is_admin, mesh_roles, joined_at, last_seen.
        'nodes', COALESCE(
            (SELECT jsonb_agg(
                    _build_membership(nmm.node_id, nmm.mesh_id)
                    ORDER BY nmm.joined_at ASC
                )
             FROM   node_mesh_memberships nmm
             WHERE  nmm.mesh_id = m.id),
            '[]'::JSONB),
        'predicates', COALESCE(
            (SELECT jsonb_agg(_build_predicate(nmp.predicate_id) ORDER BY nmp.position)
             FROM   node_mesh_predicates nmp
             WHERE  nmp.mesh_id = m.id),
            '[]'::JSONB)
    )
    FROM node_meshes m
    WHERE m.id = p_id;
$$;

-- ============================================================================
-- NodeMeshMembershipRepo
-- mesh_roles input is a plain INT array [0, 2, ...] (ordinals from Python enum).
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_node_mesh_memberships()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_membership(node_id, mesh_id)
    FROM   node_mesh_memberships
    ORDER  BY mesh_id, node_id;
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

        INSERT INTO node_mesh_memberships
               (node_id, mesh_id, mesh_roles,
                is_admin, is_anchor, is_root, joined_at, last_seen)
        VALUES (
            (v_row->>'node_id')::UUID,
            (v_row->>'mesh_id')::UUID,
            v_ordinals,
            COALESCE((v_row->>'is_admin')::BOOLEAN,  FALSE),
            COALESCE((v_row->>'is_anchor')::BOOLEAN, FALSE),
            COALESCE((v_row->>'is_root')::BOOLEAN,   FALSE),
            (v_row->>'joined_at')::TIMESTAMPTZ,
            CASE WHEN v_row->>'last_seen' IS NOT NULL
                 THEN (v_row->>'last_seen')::TIMESTAMPTZ END
        );

        RETURN NEXT _build_membership(
            (v_row->>'node_id')::UUID, (v_row->>'mesh_id')::UUID);
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
        WHERE node_id = (v_row->>'node_id')::UUID
          AND mesh_id = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('membership (%s,%s) not found',
                                       v_row->>'node_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT _build_membership(
            (v_row->>'node_id')::UUID, (v_row->>'mesh_id')::UUID);
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
            (v_row->>'node_id')::UUID, (v_row->>'mesh_id')::UUID);

        DELETE FROM node_mesh_memberships
        WHERE node_id = (v_row->>'node_id')::UUID
          AND mesh_id = (v_row->>'mesh_id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('membership (%s,%s) not found',
                                       v_row->>'node_id', v_row->>'mesh_id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- MeshRepo
-- 'status' in the input dict is a NodeMeshStatus object {name, ordinal, ...}
-- or a plain ordinal integer; we extract the ordinal either way.
-- 'nodes' contains NodeMeshMembership dicts (not NodeDevice dicts).
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
    v_status  INT;
    v_dev     JSONB;
    v_pred    JSONB;
    v_pred_id UUID;
    v_pos     INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_mesh_id := (v_row->>'id')::UUID;

        -- status may be a full NodeMeshStatus object or a plain ordinal integer
        v_status := CASE jsonb_typeof(v_row->'status')
                        WHEN 'object' THEN (v_row->'status'->>'ordinal')::INT
                        WHEN 'number' THEN (v_row->>'status')::INT
                        ELSE 0
                    END;

        INSERT INTO node_meshes (id, name, status, description, api_version)
        VALUES (
            v_mesh_id,
            v_row->>'name',
            v_status,
            v_row->>'description',
            v_row->>'api_version'
        );

        -- nodes[] are NodeMeshMembership dicts matching NodeMesh.FIELD_TYPES.
        -- Each element: {node_id, mesh_id, mesh_roles, is_admin, is_anchor,
        --                is_root, joined_at, last_seen}
        -- The referenced node_devices row must already exist (NodeDevice is
        -- registered independently via NodeDeviceRepo before joining a mesh).
        FOR v_dev IN SELECT jsonb_array_elements(v_row->'nodes') LOOP
            INSERT INTO node_mesh_memberships
                   (node_id, mesh_id, mesh_roles,
                    is_admin, is_anchor, is_root, joined_at, last_seen)
            VALUES (
                (v_dev->>'node_id')::UUID,
                v_mesh_id,
                COALESCE(
                    ARRAY(
                        SELECT CASE jsonb_typeof(elem)
                                   WHEN 'object' THEN (elem->>'ordinal')::INT
                                   WHEN 'number' THEN elem::TEXT::INT
                               END
                        FROM jsonb_array_elements(v_dev->'mesh_roles') elem
                    ),
                    '{}'::INT[]
                ),
                COALESCE((v_dev->>'is_admin')::BOOLEAN,  FALSE),
                COALESCE((v_dev->>'is_anchor')::BOOLEAN, FALSE),
                COALESCE((v_dev->>'is_root')::BOOLEAN,   FALSE),
                COALESCE((v_dev->>'joined_at')::TIMESTAMPTZ,CURRENT_TIMESTAMP),
                CASE WHEN v_dev->>'last_seen' IS NOT NULL
                     THEN (v_dev->>'last_seen')::TIMESTAMPTZ END
            )
            ON CONFLICT (node_id, mesh_id) DO UPDATE
                SET mesh_roles = EXCLUDED.mesh_roles,
                    is_admin   = EXCLUDED.is_admin,
                    is_anchor  = EXCLUDED.is_anchor,
                    is_root    = EXCLUDED.is_root,
                    last_seen  = EXCLUDED.last_seen;
        END LOOP;

        -- predicates[] are Predicate dicts with Metadata fields dissolved in.
        -- id, name, is_active, created_at, modified_at, description,
        -- predicate_type, predicate_family, <geometry keys>
        v_pos := 0;
        FOR v_pred IN SELECT jsonb_array_elements(v_row->'predicates') LOOP
            v_pred_id := gen_random_uuid();

            INSERT INTO predicates (
                id, name, is_active, created_at, modified_at, description,
                predicate_type, predicate_family
            )
            VALUES (
                v_pred_id,
                v_pred->>'name',
                COALESCE((v_pred->>'is_active')::BOOLEAN, TRUE),
                (v_pred->>'created_at')::TIMESTAMPTZ,
                (v_pred->>'modified_at')::TIMESTAMPTZ,
                v_pred->>'description',
                (v_pred->>'predicate_type')::smallint,
                (v_pred->>'predicate_family')::smallint
            )
            ON CONFLICT (id) DO UPDATE
                SET name             = EXCLUDED.name,
                    is_active        = EXCLUDED.is_active,
                    modified_at      = EXCLUDED.modified_at,
                    description      = EXCLUDED.description;

            -- Route to family child table
            IF (v_pred->>'predicate_family')::smallint = 0 THEN
                INSERT INTO predicate_geometric (predicate_id, geometry)
                VALUES (v_pred_id, _extract_geometry(v_pred))
                ON CONFLICT (predicate_id) DO UPDATE
                    SET geometry = EXCLUDED.geometry;
            END IF;

            INSERT INTO node_mesh_predicates (mesh_id, predicate_id, position)
            VALUES (v_mesh_id, v_pred_id, v_pos)
            ON CONFLICT DO NOTHING;

            v_pos := v_pos + 1;
        END LOOP;

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

        v_status := CASE jsonb_typeof(v_row->'status')
                        WHEN 'object' THEN (v_row->'status'->>'ordinal')::INT
                        WHEN 'number' THEN (v_row->>'status')::INT
                        ELSE NULL
                    END;

        UPDATE node_meshes
        SET name        = COALESCE(v_row->>'name',        name),
            status      = COALESCE(v_status,              status),
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