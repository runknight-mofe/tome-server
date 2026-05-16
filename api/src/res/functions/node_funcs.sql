-- Build a fully-populated DeviceType JSONB from an ordinal.
-- Includes all columns: name, description, manufacturer, ranging_method,
-- supports_aoa, max_update_rate_hz, typical_accuracy_m.
CREATE OR REPLACE FUNCTION _build_device_type(p_ordinal INT)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'ordinal',            dt.ordinal,
        'name',               dt.name,
        'description',        dt.description,
        'manufacturer',       dt.manufacturer,
        'ranging_method',     dt.ranging_method,
        'supports_aoa',       dt.supports_aoa,
        'max_update_rate_hz', dt.max_update_rate_hz,
        'typical_accuracy_m', dt.typical_accuracy_m
    )
    FROM device_types dt
    WHERE dt.ordinal = p_ordinal;
$$;

-- -------------------------------------------------------
-- Build a fully-populated NodeDevice JSONB.
-- 'type' is a complete DeviceType sub-object.
CREATE OR REPLACE FUNCTION _build_node_device(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',          nd.id::TEXT,
        'name',        nd.name,
        'description', nd.description,
        'is_emulated', nd.is_emulated,
        'type',        _build_device_type(nd.type)
    )
    FROM node_devices nd
    WHERE nd.id = p_id;
$$;

-- ============================================================================
-- DeviceTypeRepo
-- Input dicts carry all DeviceType fields including the capability profile.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_device_types()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_device_type(ordinal) FROM device_types ORDER BY ordinal;
$$;

CREATE OR REPLACE FUNCTION add_many_device_types(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE v_row JSONB;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO device_types (
            ordinal, name, description, manufacturer,
            ranging_method, supports_aoa,
            max_update_rate_hz, typical_accuracy_m
        )
        VALUES (
            (v_row->>'ordinal')::INT,
             v_row->>'name',
             v_row->>'description',
             v_row->>'manufacturer',
            COALESCE(v_row->>'ranging_method', 0),
            COALESCE((v_row->>'supports_aoa')::BOOLEAN,  FALSE),
            (v_row->>'max_update_rate_hz')::FLOAT8,
            (v_row->>'typical_accuracy_m')::FLOAT8
        )
        ON CONFLICT (ordinal) DO NOTHING;

        RETURN NEXT _build_device_type((v_row->>'ordinal')::INT);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_device_types(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        UPDATE device_types
        SET name               = COALESCE(v_row->>'name',               name),
            description        = COALESCE(v_row->>'description',        description),
            manufacturer       = COALESCE(v_row->>'manufacturer',       manufacturer),
            ranging_method     = COALESCE(v_row->>'ranging_method',     ranging_method),
            supports_aoa       = COALESCE((v_row->>'supports_aoa')::BOOLEAN, supports_aoa),
            max_update_rate_hz = COALESCE((v_row->>'max_update_rate_hz')::FLOAT8, max_update_rate_hz),
            typical_accuracy_m = COALESCE((v_row->>'typical_accuracy_m')::FLOAT8, typical_accuracy_m)
        WHERE ordinal = (v_row->>'ordinal')::INT;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('device_type ordinal %s not found', v_row->>'ordinal');
        END IF;
        RETURN NEXT _build_device_type((v_row->>'ordinal')::INT);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_device_types(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_device_type((v_row->>'ordinal')::INT);
        DELETE FROM device_types WHERE ordinal = (v_row->>'ordinal')::INT;
        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('device_type ordinal %s not found', v_row->>'ordinal');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- NodeDeviceRepo
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_node_devices()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_node_device(id) FROM node_devices ORDER BY id;
$$;

CREATE OR REPLACE FUNCTION add_many_node_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE v_row JSONB;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO node_devices (id, name, description, type, is_emulated)
        VALUES (
            (v_row->>'id')::UUID,
             v_row->>'name',
             v_row->>'description',
            (v_row->'type'->>'ordinal')::INT,
            (v_row->>'is_emulated')::BOOLEAN
        )
        ON CONFLICT (id) DO UPDATE
            SET name        = EXCLUDED.name,
                description = EXCLUDED.description,
                type        = EXCLUDED.type,
                is_emulated = EXCLUDED.is_emulated;

        RETURN NEXT _build_node_device((v_row->>'id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_node_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        UPDATE node_devices
        SET name        = COALESCE(v_row->>'name',                   name),
            description = COALESCE(v_row->>'description',            description),
            type        = COALESCE((v_row->'type'->>'ordinal')::INT, type),
            is_emulated = COALESCE((v_row->>'is_emulated')::BOOLEAN, is_emulated)
        WHERE id = (v_row->>'id')::UUID;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('node_device id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT _build_node_device((v_row->>'id')::UUID);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_node_devices(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_snap := _build_node_device((v_row->>'id')::UUID);
        DELETE FROM node_devices WHERE id = (v_row->>'id')::UUID;
        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('node_device id %s not found', v_row->>'id');
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;