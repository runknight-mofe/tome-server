-- -------------------------------------------------------
-- Build a Metadata JSONB.
CREATE OR REPLACE FUNCTION _build_metadata(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',          m.id::TEXT,
        'name',        m.name,
        'is_active',   m.is_active,
        'created_at',  to_char(m.created_at,  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'modified_at', to_char(m.modified_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'description', m.description
    )
    FROM predicate_metadata m
    WHERE m.id = p_id;
$$;

-- -------------------------------------------------------
-- Build a typed Predicate JSONB (any subtype).
-- Build a Predicate JSONB by joining base table to the appropriate family
-- child table.  The geometry JSONB is returned as-is; Python from_dict()
-- reconstructs the typed sub-object (Vector3D, etc.) from it.
-- Adding a new geometric subtype requires no change here.
-- Adding a new family adds one WHEN branch and a new LEFT JOIN.
CREATE OR REPLACE FUNCTION _build_predicate(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
               'predicate_type',   p.predicate_type,
               'predicate_family', p.predicate_family,
               'metadata',         _build_metadata(p.metadata_id)
           )
           -- Merge the family-specific geometry fields into the top-level object.
           -- Each COALESCE returns '{}' when the family child row is absent so
           -- the jsonb concatenation is always valid.
           || COALESCE(g.geometry, '{}'::JSONB)
    FROM predicates p
    LEFT JOIN predicate_geometric  g ON g.predicate_id = p.id
                                     AND p.predicate_family = 0
    WHERE p.id = p_id;
$$;

-- ============================================================================
-- PredicateMetadataRepo
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_predicate_metadata()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_metadata(id) FROM predicate_metadata ORDER BY created_at;
$$;

CREATE OR REPLACE FUNCTION add_many_predicate_metadata(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE v_row JSONB;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO predicate_metadata
               (id, name, is_active, created_at, modified_at, description)
        VALUES (
            (v_row->>'id')::UUID,
             v_row->>'name',
            COALESCE((v_row->>'is_active')::BOOLEAN, TRUE),
            (v_row->>'created_at')::TIMESTAMPTZ,
            (v_row->>'modified_at')::TIMESTAMPTZ,
             v_row->>'description'
        );
        RETURN NEXT _build_metadata((v_row->>'id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_predicate_metadata(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        UPDATE predicate_metadata
        SET name        = COALESCE(v_row->>'name',        name),
            is_active   = COALESCE((v_row->>'is_active')::BOOLEAN, is_active),
            modified_at = COALESCE((v_row->>'modified_at')::TIMESTAMPTZ, modified_at),
            description = COALESCE(v_row->>'description', description)
        WHERE id = (v_row->>'id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate_metadata id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT _build_metadata((v_row->>'id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_predicate_metadata(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_metadata((v_row->>'id')::UUID);
        DELETE FROM predicate_metadata WHERE id = (v_row->>'id')::UUID;
        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate_metadata id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- PredicateRepo
--
-- Input dict contract:
--   predicate_type   smallint  -- 0, 1, 2,... (ordinals for Predicate.Type enum)
--   predicate_family smallint  -- 0, 1, 2 (ordinals for Predicate.Family enum)
--   * 0 --> GEOMETRIC
--   * 1 --> BEHAVIOR
--   * 2 --> RANGING
--   metadata         JSONB    -- embedded Metadata sub-object
--   <geometry keys>  JSONB    -- family-specific; stored as-is in the child table
--
-- geometry is assembled from the remaining keys after stripping the known
-- top-level fields (predicate_type, predicate_family, metadata, id).
-- This means no change is needed here when new geometric subtypes are added.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_predicates()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_predicate(id) FROM predicates ORDER BY metadata_id;
$$;

-- Helper: strip control keys and return the geometry portion of the input dict
CREATE OR REPLACE FUNCTION _extract_geometry(p_row JSONB)
RETURNS JSONB LANGUAGE SQL IMMUTABLE AS $$
    SELECT p_row - 'predicate_type'
                 - 'predicate_family'
                 - 'metadata'
                 - 'id';
$$;

CREATE OR REPLACE FUNCTION add_many_predicates(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row    JSONB;
    v_meta   JSONB;
    v_pid    UUID;
    v_family TEXT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_pid    := gen_random_uuid();
        v_meta   := v_row->'metadata';
        v_family := v_row->>'predicate_family';

        INSERT INTO predicate_metadata
               (id, name, is_active, created_at, modified_at, description)
        VALUES (
            (v_meta->>'id')::UUID, v_meta->>'name',
            COALESCE((v_meta->>'is_active')::BOOLEAN, TRUE),
            (v_meta->>'created_at')::TIMESTAMPTZ,
            (v_meta->>'modified_at')::TIMESTAMPTZ,
             v_meta->>'description'
        )
        ON CONFLICT (id) DO UPDATE
            SET name        = EXCLUDED.name,
                is_active   = EXCLUDED.is_active,
                modified_at = EXCLUDED.modified_at,
                description = EXCLUDED.description;

        INSERT INTO predicates (id, predicate_type, predicate_family, metadata_id)
        VALUES (v_pid, v_row->>'predicate_type', v_family, (v_meta->>'id')::UUID);

        -- Route to the correct family child table
        IF v_family = 0 THEN
            INSERT INTO predicate_geometric (predicate_id, geometry)
            VALUES (v_pid, _extract_geometry(v_row));
        -- Future families:
        -- ELSIF v_family = 'BEHAVIORAL' THEN
        --     INSERT INTO predicate_behavioral (predicate_id, config)
        --     VALUES (v_pid, _extract_geometry(v_row));
        -- ELSIF v_family = 'RANGING' THEN
        --     INSERT INTO predicate_ranging (predicate_id, config)
        --     VALUES (v_pid, _extract_geometry(v_row));
        ELSE
            RAISE SQLSTATE '22000'
                USING MESSAGE = format('Unknown predicate_family: %s', v_family);
        END IF;

        RETURN NEXT _build_predicate(v_pid);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_predicates(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row    JSONB;
    v_meta   JSONB;
    v_pid    UUID;
    v_family TEXT;
    v_cnt    INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_pid    := (v_row->>'id')::UUID;
        v_meta   := v_row->'metadata';
        v_family := v_row->>'predicate_family';

        IF v_meta IS NOT NULL THEN
            UPDATE predicate_metadata
            SET name        = COALESCE(v_meta->>'name',        name),
                is_active   = COALESCE((v_meta->>'is_active')::BOOLEAN, is_active),
                modified_at = COALESCE((v_meta->>'modified_at')::TIMESTAMPTZ, modified_at),
                description = COALESCE(v_meta->>'description', description)
            WHERE id = (v_meta->>'id')::UUID;
        END IF;

        -- Update base row if predicate_type changes (rare but valid)
        UPDATE predicates
        SET predicate_type = COALESCE(v_row->>'predicate_type', predicate_type)
        WHERE id = v_pid;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate id %s not found', v_pid);
        END IF;

        -- Merge new geometry into the child table (JSONB || merges keys)
        IF v_family = 0 THEN
            UPDATE predicate_geometric
            SET geometry = geometry || _extract_geometry(v_row)
            WHERE predicate_id = v_pid;
        END IF;

        RETURN NEXT _build_predicate(v_pid);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_predicates(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_predicate((v_row->>'id')::UUID);
        -- ON DELETE CASCADE on predicate_geometric removes the child row
        DELETE FROM predicates WHERE id = (v_row->>'id')::UUID;
        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('predicate id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;