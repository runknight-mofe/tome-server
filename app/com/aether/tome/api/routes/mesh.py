from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR
import logging
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
import requests
from com.aether.tome.api.schema.device_schema import device_schema
from com.aether.tome.api.service.mesh import add_predicate_to_node_mesh, join_device_to_node_mesh, remove_device_from_node_mesh, remove_predicate_to_node_mesh, retrieve_mesh
from com.aether.tome.api.tome_server import resp_ok
from com.aether.tome.api.tome_config import config

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

mesh_bp = Blueprint('mesh', __name__)

@mesh_bp.route("/get/<string:id>")
def get_mesh(id):
    uid = UUID(id)
    mesh = retrieve_mesh(uid)
    if mesh:
        return resp_ok({"mesh":mesh.to_dict()})
    return resp_ok({})