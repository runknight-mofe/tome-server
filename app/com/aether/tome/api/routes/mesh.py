from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR
import logging
from uuid import UUID

from flask import Blueprint, abort, jsonify, request

from com.aether.tome.api.schema.mesh_schema import (
    mesh_membership_schema,
    mesh_predicate_membership_schema,
)
from com.aether.tome.api.service.mesh import (
    join_device_to_node_mesh,
    join_predicate_to_mesh,
    remove_device_from_node_mesh,
    remove_predicate_from_mesh,
    retrieve_mesh,
    update_predicate_position_in_mesh,
)
from com.aether.tome.api.tome_server import resp_ok
from com.aether.tome.api.tome_config import config

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

mesh_bp = Blueprint('mesh', __name__)


# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------

@mesh_bp.route("/get/<string:id>", methods=["GET"])
def get_mesh(id):
    uid = UUID(id)
    mesh = retrieve_mesh(uid)
    return resp_ok({"mesh": mesh.to_dict()} if mesh else {})


# ---------------------------------------------------------------------------
# Device membership
# ---------------------------------------------------------------------------

@mesh_bp.route("/device/join", methods=["POST"])
def join_device():
    req = mesh_membership_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate mesh membership request")
    membership = join_device_to_node_mesh(req)
    if not membership:
        abort(INTERNAL_SERVER_ERROR, f"Unable to add device {req.device_id} to mesh {req.mesh_id}")
    return resp_ok({"membership": membership.to_dict()})


@mesh_bp.route("/device/leave", methods=["POST"])
def leave_device():
    req = mesh_membership_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate mesh membership request")
    removed = remove_device_from_node_mesh(req)
    if not removed:
        abort(INTERNAL_SERVER_ERROR, f"Unable to remove device {req.device_id} from mesh {req.mesh_id}")
    return resp_ok({})


# ---------------------------------------------------------------------------
# Predicate membership
# ---------------------------------------------------------------------------

@mesh_bp.route("/predicate/join", methods=["POST"])
def join_predicate():
    req = mesh_predicate_membership_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate predicate membership request")
    membership = join_predicate_to_mesh(req)
    if not membership:
        abort(INTERNAL_SERVER_ERROR,
              f"Unable to add predicate {req.predicate_id} to mesh {req.mesh_id}")
    return resp_ok({"membership": membership.to_dict()})


@mesh_bp.route("/predicate/leave", methods=["POST"])
def leave_predicate():
    req = mesh_predicate_membership_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate predicate membership request")
    removed = remove_predicate_from_mesh(req)
    if not removed:
        abort(INTERNAL_SERVER_ERROR,
              f"Unable to remove predicate {req.predicate_id} from mesh {req.mesh_id}")
    return resp_ok({})


@mesh_bp.route("/predicate/update", methods=["POST"])
def update_predicate():
    req = mesh_predicate_membership_schema.load_data(request.get_json())
    if not req:
        abort(BAD_REQUEST, "Unable to validate predicate membership request")
    updated = update_predicate_position_in_mesh(req)
    if not updated:
        abort(INTERNAL_SERVER_ERROR,
              f"Unable to update predicate {req.predicate_id} in mesh {req.mesh_id}")
    return resp_ok({"membership": updated.to_dict()})
