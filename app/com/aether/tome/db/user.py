from datetime import datetime, timedelta, timezone
from uuid import UUID

from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.user import User, UserSession


class UserRepo(BaseRepository[User]):
    """Repository for User principals."""

    __model__ = User
    KEYS = [User.ID, User.USERNAME]

    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(UserRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_users"
        self.sql[self.ADD]    = "add_many_users"
        self.sql[self.UPDATE] = "update_many_users"
        self.sql[self.REMOVE] = "remove_many_users"

    def get_or_create(self, username: str,
                      display_name: str | None = None) -> User | None:
        """
        Idempotent user registration.

        Looks up by username first; creates only if not found.  Used when a
        user authenticates via the external identity provider for the first
        time.

        Args:
            username:     Unique login handle from the identity provider
            display_name: Human-readable name (defaults to username)

        Returns:
            User (existing or newly created), or None on error
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_or_create; repo not initialized')

        existing = self.get(username, field=User.USERNAME)
        if existing:
            return existing

        user = User({
            User.ID           : None,
            User.USERNAME     : username,
            User.DISPLAY_NAME : display_name or username,
            User.CREATED_AT   : None,
        })
        result = self.add(user)
        if result:
            self.logger.info(f"User registered: {result.username} ({result.id})")
        else:
            self.logger.error(f"Failed to register user {username}")
        return result

    def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their login handle."""
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_by_username; repo not initialized')
        return self.get(username, field=User.USERNAME)


class UserSessionRepo(BaseRepository[UserSession]):
    """
    Repository for UserSession records.

    Enforces the invariant that a user has at most one active session at a
    time (and therefore acts through at most one device at a time).  The DB
    carries a partial unique index on (user_id) WHERE is_active = TRUE as a
    belt-and-suspenders constraint.
    """

    __model__ = UserSession
    KEYS = [UserSession.ID]

    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(UserSessionRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_user_sessions"
        self.sql[self.ADD]    = "add_many_user_sessions"
        self.sql[self.UPDATE] = "update_many_user_sessions"
        self.sql[self.REMOVE] = "remove_many_user_sessions"

    # -----------------------------------------------------------------------
    # Workflow 1: Create a new session
    # -----------------------------------------------------------------------
    def create_session(self, user_id: UUID, device_id: UUID,
                       duration_hours: int = 24) -> UserSession | None:
        """
        Establish a new active session for a user on a specific device.

        Before creating, any existing active session for this user is expired
        so the one-active-session-per-user invariant is maintained.

        Args:
            user_id:        UUID of the authenticated user
            device_id:      UUID of the device the user is acting through
            duration_hours: How many hours until hard expiry (default 24)

        Returns:
            Newly created UserSession, or None on failure
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.create_session; repo not initialized')

        # Expire any existing active session for this user
        existing = self.get_active_session_for_user(user_id)
        if existing:
            self.logger.info(
                f"Expiring existing session {existing.id} for user {user_id} "
                f"before creating new one on device {device_id}"
            )
            self.expire_session(existing.id)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=duration_hours)

        session = UserSession({
            UserSession.ID             : None,
            UserSession.USER_ID        : user_id,
            UserSession.DEVICE_ID      : device_id,
            UserSession.CREATED_AT     : None,
            UserSession.EXPIRES_AT     : expires_at.isoformat(),
            UserSession.LAST_ACTIVE_AT : None,
            UserSession.IS_ACTIVE      : True,
        })
        return self.add(session)

    # -----------------------------------------------------------------------
    # Workflow 2: Expire a session (soft delete)
    # -----------------------------------------------------------------------
    def expire_session(self, session_id: UUID) -> UserSession | None:
        """
        Mark a session as inactive.

        Does not delete the record; the history is preserved.  Callers are
        responsible for dropping any NodeMeshMembership records backed by
        this session (see NodeMeshMembershipRepo.drop_memberships_for_session).

        Args:
            session_id: UUID of the session to expire

        Returns:
            Updated UserSession with is_active=False, or None if not found
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.expire_session; repo not initialized')

        session = self.get(session_id)
        if not session:
            return None
        session.is_active = False
        return self.update(session)

    # -----------------------------------------------------------------------
    # Workflow 3: Heartbeat — extend inactivity window
    # -----------------------------------------------------------------------
    def touch_session(self, session_id: UUID) -> UserSession | None:
        """
        Update last_active_at to the current time.

        Call this on each authenticated API request to prevent inactivity
        expiry.

        Args:
            session_id: UUID of the session to touch

        Returns:
            Updated UserSession, or None if not found / already expired
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.touch_session; repo not initialized')

        session = self.get(session_id)
        if not session or not session.is_active:
            return None
        session.last_active_at = datetime.now(timezone.utc)
        return self.update(session)

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------
    def get_active_session_for_user(self, user_id: UUID) -> UserSession | None:
        """
        Return the single active session for a user, or None.

        The partial unique index guarantees at most one result.

        Args:
            user_id: UUID of the user

        Returns:
            Active UserSession, or None if no active session exists
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_active_session_for_user; repo not initialized')

        with self._lock:
            for s in self.all_items:
                if s.user_id == user_id and s.is_active:
                    return s
        return None

    def get_active_session_for_device(self, device_id: UUID) -> UserSession | None:
        """
        Return the active session currently bound to a device, or None.

        Args:
            device_id: UUID of the device

        Returns:
            Active UserSession, or None if the device has no active session
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_active_session_for_device; repo not initialized')

        with self._lock:
            for s in self.all_items:
                if s.device_id == device_id and s.is_active:
                    return s
        return None

    def get_sessions_for_user(self, user_id: UUID) -> set[UserSession]:
        """All sessions (active and historical) for a user."""
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_sessions_for_user; repo not initialized')

        with self._lock:
            return {s for s in self.all_items if s.user_id == user_id}

    def is_session_valid(self, session_id: UUID) -> bool:
        """
        True if the session exists, is active, and has not passed its expiry.

        Args:
            session_id: UUID of the session to check

        Returns:
            bool
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.is_session_valid; repo not initialized')

        session = self.get(session_id)
        if not session:
            return False
        return not session.is_expired()
