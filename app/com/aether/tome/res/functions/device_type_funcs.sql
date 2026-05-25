-- ============================================================================
-- Aether / Tome Server — node_funcs.sql
-- Functions for DeviceTypeRepo and NodeDeviceRepo.
--
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
            COALESCE((v_row->>'ranging_method')::INT, 0),
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
            ranging_method     = COALESCE((v_row->>'ranging_method')::INT, ranging_method),
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