-- ============================================================================
-- Aether / Tome Server — predicate_funcs.sql
-- Functions for PredicateRepo.
--
-- Metadata fields (name, is_active, created_at, modified_at, description) are
-- stored directly on the predicates table.  There is no predicate_metadata
-- table and no _build_metadata helper.  All fields are emitted directly by
-- _build_predicate, consistent with how name/description are handled on every
-- other model class.
--
-- predicate_type   smallint — Predicate.Type enum ordinal
--   0=POINT  1=LINE_SEGMENT  2=PLANE  3=SPHERE  4=BOX
--
-- predicate_family smallint — Predicate.Family enum ordinal
--   0=GEOMETRIC  1=BEHAVIOR  2=RANGING
--
-- Input dict contract:
--   id               str (UUID)
--   name             str
--   is_active        bool
--   created_at       ISO8601 str
--   modified_at      ISO8601 str
--   description      str | null
--   predicate_type   int  (Type ordinal)
--   predicate_family int  (Family ordinal)
--   <geometry keys>  — family-specific; stored as-is in the child table
--
-- geometry is assembled by _extract_geometry() which strips the known
-- control keys.  No change is needed here when new geometric subtypes are
-- added — the stripping is key-agnostic.
-- ============================================================================

-- -------------------------------------------------------
-- Build a typed Predicate JSONB by joining base table to the appropriate
-- family child table.  The geometry JSONB is returned as-is so Python
-- from_dict() can reconstruct the typed sub-object (Vector3D, etc.).
-- Adding a new geometric subtype requires no change here.
-- Adding a new family adds one WHEN branch and a new LEFT JOIN.
CREATE OR REPLACE FUNCTION _build_predicate(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
               -- Metadata fields (dissolved into predicates table)
               'id',             p.id::TEXT,
               'name',           p.name,
               'is_active',      p.is_active,
               'created_at',     to_char(p.created_at,  'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
               'modified_at',    to_char(p.modified_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
               'description',    p.description,
               -- Predicate discriminators (smallint ordinals)
               'predicate_type',   p.predicate_type,
               'predicate_family', p.predicate_family
           )
           -- Merge the family-specific geometry fields into the top-level object.
           -- COALESCE returns '{}' when the family child row is absent so the
           -- jsonb concatenation is always valid.
           || COALESCE(g.geometry, '{}'::JSONB)
    FROM predicates p
    LEFT JOIN predicate_geometric  g ON g.predicate_id = p.id
                                     AND p.predicate_family = 0
    WHERE p.id = p_id;
$$;

-- Helper: strip control keys and return the geometry portion of the input dict.
-- This is key-agnostic: any keys not in the exclusion list pass through as
-- geometry data, so new subtypes require zero changes here.
CREATE OR REPLACE FUNCTION _extract_geometry(p_row JSONB)
RETURNS JSONB LANGUAGE SQL IMMUTABLE AS $$
    SELECT p_row - 'id'
                 - 'name'
                 - 'is_active'
                 - 'created_at'
                 - 'modified_at'
                 - 'description'
                 - 'predicate_type'
                 - 'predicate_family';
$$;

-- ============================================================================
-- PredicateRepo
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_predicates()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_predicate(id) FROM predicates ORDER BY created_at;
$$;

CREATE OR REPLACE FUNCTION add_many_predicates(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row    JSONB;
    v_pid    UUID;
    v_family smallint;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_pid    := (v_row->>'id')::UUID;
        v_family := (v_row->>'predicate_family')::smallint;
 
        INSERT INTO predicates (
            id, name, is_active, created_at, modified_at, description,
            predicate_type, predicate_family
        )
        VALUES (
            v_pid,
            v_row->>'name',
            COALESCE((v_row->>'is_active')::BOOLEAN, TRUE),
            (v_row->>'created_at')::TIMESTAMPTZ,
            (v_row->>'modified_at')::TIMESTAMPTZ,
            v_row->>'description',
            (v_row->>'predicate_type')::smallint,
            v_family
        );
 
        -- Route to the correct family child table
        IF v_family = 0 THEN            -- GEOMETRIC
            INSERT INTO predicate_geometric (predicate_id, geometry)
            VALUES (v_pid, _extract_geometry(v_row));
        -- Future families:
        -- ELSIF v_family = 1 THEN      -- BEHAVIOR
        --     INSERT INTO predicate_behavioral (predicate_id, config)
        --     VALUES (v_pid, _extract_geometry(v_row));
        -- ELSIF v_family = 2 THEN      -- RANGING
        --     INSERT INTO predicate_ranging (predicate_id, config)
        --     VALUES (v_pid, _extract_geometry(v_row));
        ELSE
            RAISE SQLSTATE '22000'
                USING MESSAGE = format('Unknown predicate_family ordinal: %s', v_family);
        END IF;
 
        RETURN NEXT _build_predicate(v_pid);
    END LOOP;
END;
$$;

REATE OR REPLACE FUNCTION update_many_predicates(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row    JSONB;
    v_pid    UUID;
    v_family smallint;
    v_cnt    INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_pid    := (v_row->>'id')::UUID;
        v_family := (v_row->>'predicate_family')::smallint;
 
        UPDATE predicates
        SET name             = COALESCE(v_row->>'name',                         name),
            is_active        = COALESCE((v_row->>'is_active')::BOOLEAN,         is_active),
            modified_at      = COALESCE((v_row->>'modified_at')::TIMESTAMPTZ,   modified_at),
            description      = COALESCE(v_row->>'description',                  description),
            predicate_type   = COALESCE((v_row->>'predicate_type')::smallint,   predicate_type)
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