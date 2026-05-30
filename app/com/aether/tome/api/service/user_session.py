"""
User and session management service.

This service manages local User records (created from external IdP identities)
and UserSession records that authorise a user's presence on a specific device.

Session lifecycle
-----------------
1. User authenticates against the external auth service.
2. Client calls create_session(user_id, device_id) to establish a local session.
3. The session_id is used in all subsequent mesh join/leave requests.
4. On logout (or inactivity expiry), expire_session_and_drop_memberships() is
   called, which marks the session inactive and removes all mesh memberships
   that were backed by that session.
"""

from uuid import UUID

from com.aether.tome.api.tome_config import config
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.user import UserRepo, UserSessionRepo
from com.aether.tome.db.mesh import NodeMeshMembershipRepo
from com.aether.tome.model.user import User, UserSession

DB_PARAMS = {
    DBConnector.HOST : config.db_host,
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB   : config.db_name,
    DBConnector.PASS : config.db_pass,
}

ur  = UserRepo(db_params=DB_PARAMS)
usr = UserSessionRepo(db_params=DB_PARAMS)
mmr = NodeMeshMembershipRepo(db_params=DB_PARAMS)

assert ur.initialize() and usr.initialize() and mmr.initialize(), \
    "One or more repos failed to initialize"


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def get_or_create_user(username: str,
                       display_name: str | None = None) -> User | None:
    """
    Idempotent user registration from an external identity provider.

    Args:
        username:     Unique login handle (from IdP)
        display_name: Optional human-readable name (defaults to username)

    Returns:
        User (existing or newly created), or None on error
    """
    return ur.get_or_create(username, display_name=display_name)


def get_user_by_id(user_id: UUID) -> User | None:
    """Retrieve a user by their unique identifier."""
    return ur.get(user_id)


def get_user_by_username(username: str) -> User | None:
    """Retrieve a user by their login handle."""
    return ur.get_by_username(username)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(user_id: UUID, device_id: UUID,
                   duration_hours: int = 24) -> UserSession | None:
    """
    Establish a new session for a user on a specific device.

    Any existing active session for this user is expired first, enforcing the
    one-active-session-per-user invariant.

    Args:
        user_id:        UUID of the authenticated user
        device_id:      UUID of the device the user is acting through
        duration_hours: Session hard-expiry window in hours (default 24)

    Returns:
        Newly created UserSession, or None on failure
    """
    return usr.create_session(user_id, device_id, duration_hours=duration_hours)


def get_session(session_id: UUID) -> UserSession | None:
    """Retrieve a session by its unique identifier."""
    return usr.get(session_id)


def is_session_valid(session_id: UUID) -> bool:
    """
    True if the session exists, is active, and has not passed its hard expiry.

    Args:
        session_id: UUID of the session to validate

    Returns:
        bool
    """
    return usr.is_session_valid(session_id)


def touch_session(session_id: UUID) -> UserSession | None:
    """
    Refresh last_active_at to prevent inactivity expiry.

    Call this on each authenticated request made under this session.

    Args:
        session_id: UUID of the session to heartbeat

    Returns:
        Updated UserSession, or None if expired/not found
    """
    return usr.touch_session(session_id)


def expire_session_and_drop_memberships(session_id: UUID) -> bool:
    """
    Expire a session and remove all mesh memberships it backed.

    This is the canonical path for logout and session expiry.  After this
    call:
    - UserSession.is_active == False
    - All NodeMeshMembership rows with this session_id are removed
    - The associated device is no longer present in any mesh

    Args:
        session_id: UUID of the session to expire

    Returns:
        True if the session was found and expired, False otherwise
    """
    dropped = mmr.drop_memberships_for_session(session_id)
    if dropped:
        pass  # Memberships removed; proceed to expire the session

    expired = usr.expire_session(session_id)
    return expired is not None


def get_active_session_for_user(user_id: UUID) -> UserSession | None:
    """Return the single active session for a user, or None."""
    return usr.get_active_session_for_user(user_id)


def get_active_session_for_device(device_id: UUID) -> UserSession | None:
    """Return the active session currently bound to a device, or None."""
    return usr.get_active_session_for_device(device_id)


def get_user_sessions(user_id: UUID) -> set[UserSession]:
    """Return all sessions (active and historical) for a user."""
    return usr.get_sessions_for_user(user_id)
