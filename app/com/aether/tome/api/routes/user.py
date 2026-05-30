import logging
from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND
from uuid import UUID

from flask import Blueprint, jsonify, request, abort
import requests

from com.aether.tome.api.tome_config import config
from com.aether.tome.api.tome_server import forward_to_auth, resp_ok
from com.aether.tome.api.schema.user_schema import (
    create_user_schema,
    create_user_session_schema,
)
from com.aether.tome.api.service.user_session import (
    get_or_create_user,
    get_user_by_id,
    get_user_by_username,
    create_session,
    get_session,
    is_session_valid,
    touch_session,
    expire_session_and_drop_memberships,
    get_active_session_for_user,
    get_user_sessions,
)

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

user_bp = Blueprint('user', __name__)


# ---------------------------------------------------------------------------
# External auth delegation (unchanged)
# ---------------------------------------------------------------------------

@user_bp.route("/user")
def get_user():
    """Forward authentication check to the external identity provider."""
    try:
        url = f"{config.auth_api_url}/auth/user"
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}
        resp = requests.get(url, headers=headers, cookies=request.cookies)

        json_data = {}
        if resp.status_code == 200:
            user = resp.json()
            if user and user.get("username"):
                json_data = user
            else:
                json_data = {"authenticated": False}
        else:
            json_data = {"authenticated": False}

        response = jsonify(json_data)
        response.headers["Connection"] = "keep-alive"
        response.headers["Content-Length"] = str(len(response.get_data()))
        return response
    except Exception:
        response = jsonify({"authenticated": False})
        response.headers["Connection"] = "keep-alive"
        return response


@user_bp.route("/logout", methods=["POST"])
def logout():
    """Log the user out of the external identity provider and expire any active local session."""
    # Expire the local session first so mesh memberships are cleaned up
    session_id_str = request.json.get("session_id") if request.json else None
    if session_id_str:
        try:
            expire_session_and_drop_memberships(UUID(session_id_str))
        except Exception as e:
            logger.warning(f"Failed to expire local session on logout: {e}")

    return forward_to_auth("/auth/logout", method="POST")


@user_bp.route("/redirect")
def redirect():
    next_url = request.args.get("next", "/")
    return forward_to_auth(f"/auth/redirect?next={next_url}")


# ---------------------------------------------------------------------------
# Local user registry
# ---------------------------------------------------------------------------

@user_bp.route("/register", methods=["POST"])
def register_user():
    """
    Register or retrieve a local user record.

    Call this after successful external authentication to ensure a local User
    record exists for the authenticated identity.

    Body: { "username": "...", "display_name": "..." (optional) }
    """
    req = create_user_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate user registration request")

    user = get_or_create_user(req.username, display_name=getattr(req, 'display_name', None))
    if not user:
        abort(INTERNAL_SERVER_ERROR, f"Unable to register user {req.username}")
    return resp_ok({"user": user.to_dict()})


@user_bp.route("/<string:user_id>", methods=["GET"])
def get_user_by_id_route(user_id):
    """Retrieve a local user record by UUID."""
    user = get_user_by_id(UUID(user_id))
    if not user:
        abort(NOT_FOUND, f"User {user_id} not found")
    return resp_ok({"user": user.to_dict()})


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@user_bp.route("/session", methods=["POST"])
def create_user_session():
    """
    Establish a new session for a user on a specific device.

    Any existing active session for the user is expired first (one-active-
    session-per-user invariant).

    Body: { "user_id": "...", "device_id": "...", "duration_hours": 24 }
    """
    req = create_user_session_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate session creation request")

    session = create_session(req.user_id, req.device_id,
                             duration_hours=req.duration_hours)
    if not session:
        abort(INTERNAL_SERVER_ERROR,
              f"Unable to create session for user {req.user_id} on device {req.device_id}")
    return resp_ok({"session": session.to_dict()})


@user_bp.route("/session/<string:session_id>", methods=["GET"])
def get_session_route(session_id):
    """Retrieve a session record by UUID."""
    session = get_session(UUID(session_id))
    if not session:
        abort(NOT_FOUND, f"Session {session_id} not found")
    return resp_ok({"session": session.to_dict(),
                    "valid": not session.is_expired()})


@user_bp.route("/session/<string:session_id>/expire", methods=["POST"])
def expire_session_route(session_id):
    """
    Expire a session and drop all mesh memberships it backed.

    Use this for explicit logout or when the client detects inactivity expiry.
    """
    ok = expire_session_and_drop_memberships(UUID(session_id))
    if not ok:
        abort(NOT_FOUND, f"Session {session_id} not found or already expired")
    return resp_ok({})


@user_bp.route("/session/<string:session_id>/touch", methods=["POST"])
def touch_session_route(session_id):
    """Refresh the last_active_at timestamp to keep the session alive."""
    session = touch_session(UUID(session_id))
    if not session:
        abort(NOT_FOUND, f"Session {session_id} not found or already expired")
    return resp_ok({"session": session.to_dict()})


@user_bp.route("/<string:user_id>/sessions", methods=["GET"])
def get_user_sessions_route(user_id):
    """List all sessions (active and historical) for a user."""
    sessions = get_user_sessions(UUID(user_id))
    return resp_ok({"sessions": [s.to_dict() for s in sessions]})