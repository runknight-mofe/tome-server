-- -------------------------------------------------------
-- Build a fully-populated Device JSONB.
-- 'type' is a complete DeviceType sub-object.
CREATE OR REPLACE FUNCTION _build_device(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',           nd.id::TEXT,
        'name',         nd.name,
        'description',  nd.description,
        'is_active',    nd.is_emulated,
        'is_emulated',  nd.is_emulated,
        'type',         nd.type,
        'created_at',   to_char(nd.created_at,  'YYYY-MM-DD"T"HH24:MI:SS"Z"')
    )
    FROM devices nd
    WHERE nd.id = p_id;
$$;

-- ============================================================================
-- DeviceRepo
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_devices()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_device(id) FROM devices ORDER BY created_at;
$$;

CREATE OR REPLACE FUNCTION add_many_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row   JSONB;
    v_dv_id UUID;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        -- id is owned by the DB; any value in the payload is discarded.
        -- 'type' in the input is a DeviceType dict; we store only the ordinal.
        INSERT INTO devices (name, description, type, is_active, is_emulated)
        VALUES (
             v_row->>'name',
             v_row->>'description',
            (v_row->'type')::INT,
            (v_row->>'is_active')::BOOLEAN,
            (v_row->>'is_emulated')::BOOLEAN
        )
        RETURNING id INTO v_dv_id;

        RETURN NEXT _build_device(v_dv_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        UPDATE devices
        SET name        = COALESCE(v_row->>'name',                   name),
            description = COALESCE(v_row->>'description',            description),
            type        = COALESCE((v_row->'type')::INT, type),
            is_active   = COALESCE((v_row->>'is_active')::BOOLEAN, is_active),
            is_emulated = COALESCE((v_row->>'is_emulated')::BOOLEAN, is_emulated)
        WHERE id = (v_row->>'id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('device id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT _build_device((v_row->>'id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_device((v_row->>'id')::UUID);
        DELETE FROM devices WHERE id = (v_row->>'id')::UUID;
        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('device id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;