-- ============================================================================
-- Aether / Tome Server — user_funcs.sql
--
-- Stored procedures for UserRepo and UserSessionRepo.
--
-- User:
--   Simple CRUD on the users table.
--
-- UserSession:
--   is_active / expires_at drive session validity.
--   The partial unique indexes on user_sessions guarantee one active session
--   per user and one per device at the DB level.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Helper: build a User JSONB from the users table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION _build_user(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',           u.id::TEXT,
        'username',     u.username,
        'display_name', u.display_name,
        'created_at',   to_char(u.created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
    )
    FROM users u
    WHERE u.id = p_id;
$$;

-- ---------------------------------------------------------------------------
-- Helper: build a UserSession JSONB from the user_sessions table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION _build_user_session(p_id UUID)
RETURNS JSONB LANGUAGE SQL STABLE AS $$
    SELECT jsonb_build_object(
        'id',             s.id::TEXT,
        'user_id',        s.user_id::TEXT,
        'device_id',      s.device_id::TEXT,
        'created_at',     to_char(s.created_at,     'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'expires_at',     to_char(s.expires_at,     'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'last_active_at', to_char(s.last_active_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'is_active',      s.is_active
    )
    FROM user_sessions s
    WHERE s.id = p_id;
$$;

-- ============================================================================
-- UserRepo
-- Keys: [ID, USERNAME]
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_users()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_user(id) FROM users ORDER BY username;
$$;

CREATE OR REPLACE FUNCTION add_many_users(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_id  UUID;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        INSERT INTO users (username, display_name)
        VALUES (
            v_row->>'username',
            COALESCE(v_row->>'display_name', v_row->>'username')
        )
        RETURNING id INTO v_id;

        RETURN NEXT _build_user(v_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_users(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_id  UUID;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_id := (v_row->>'id')::UUID;

        UPDATE users
        SET display_name = COALESCE(v_row->>'display_name', display_name)
        WHERE id = v_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('user id %s not found', v_id);
        END IF;
        RETURN NEXT _build_user(v_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_users(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_id   UUID;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_id   := (v_row->>'id')::UUID;
        v_snap := _build_user(v_id);

        DELETE FROM users WHERE id = v_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('user id %s not found', v_id);
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;

-- ============================================================================
-- UserSessionRepo
-- Keys: [ID]
-- ============================================================================

CREATE OR REPLACE FUNCTION get_all_user_sessions()
RETURNS SETOF JSONB LANGUAGE SQL STABLE AS $$
    SELECT _build_user_session(id)
    FROM   user_sessions
    ORDER  BY created_at DESC;
$$;

CREATE OR REPLACE FUNCTION add_many_user_sessions(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_id  UUID;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        -- created_at and last_active_at default to CURRENT_TIMESTAMP in the DB.
        -- expires_at must be supplied by the caller.
        INSERT INTO user_sessions (user_id, device_id, expires_at, is_active)
        VALUES (
            (v_row->>'user_id')::UUID,
            (v_row->>'device_id')::UUID,
            (v_row->>'expires_at')::TIMESTAMPTZ,
            COALESCE((v_row->>'is_active')::BOOLEAN, TRUE)
        )
        RETURNING id INTO v_id;

        RETURN NEXT _build_user_session(v_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION update_many_user_sessions(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row JSONB;
    v_id  UUID;
    v_cnt INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_id := (v_row->>'id')::UUID;

        UPDATE user_sessions
        SET is_active      = COALESCE((v_row->>'is_active')::BOOLEAN,       is_active),
            expires_at     = COALESCE((v_row->>'expires_at')::TIMESTAMPTZ,  expires_at),
            last_active_at = COALESCE((v_row->>'last_active_at')::TIMESTAMPTZ, last_active_at)
        WHERE id = v_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('user_session id %s not found', v_id);
        END IF;
        RETURN NEXT _build_user_session(v_id);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION remove_many_user_sessions(VARIADIC p_rows JSONB[])
RETURNS SETOF JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_row  JSONB;
    v_id   UUID;
    v_snap JSONB;
    v_cnt  INT;
BEGIN
    FOREACH v_row IN ARRAY p_rows LOOP
        v_id   := (v_row->>'id')::UUID;
        v_snap := _build_user_session(v_id);

        -- ON DELETE CASCADE removes node_mesh_memberships rows for this session
        DELETE FROM user_sessions WHERE id = v_id;

        GET DIAGNOSTICS v_cnt = ROW_COUNT;
        IF v_cnt = 0 THEN
            RAISE SQLSTATE '02000'
                USING MESSAGE = format('user_session id %s not found', v_id);
        END IF;
        RETURN NEXT v_snap;
    END LOOP;
END;
$$;
