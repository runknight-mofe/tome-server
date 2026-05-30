from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR
import logging
from uuid import UUID

from flask import Blueprint, abort, request

from com.aether.tome.api.schema.predicate_schema import create_predicate_schema
from com.aether.tome.api.service.predicate import (
    create_predicate,
    disable_predicate,
    enable_predicate,
    remove_predicate,
    retrieve_predicate,
)
from com.aether.tome.api.tome_server import resp_ok
from com.aether.tome.api.tome_config import config

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

predicate_bp = Blueprint('predicate', __name__)


@predicate_bp.route("/get/<string:id>", methods=["GET"])
def get_predicate(id):
    uid = UUID(id)
    predicate = retrieve_predicate(uid)
    return resp_ok({"predicate": predicate.to_dict()} if predicate else {})


@predicate_bp.route("/create", methods=["POST"])
def create():
    predicate = create_predicate_schema.load_data(request.get_json())
    if not predicate:
        abort(BAD_REQUEST, "Unable to validate predicate")
    created = create_predicate(predicate)
    if not created:
        abort(INTERNAL_SERVER_ERROR,
              f"Unable to create predicate {predicate.name} at this time due to server error.")
    return resp_ok({"predicate": created.to_dict()})


@predicate_bp.route("/remove/<string:id>", methods=["GET"])
def remove(id):
    uid = UUID(id)
    existing = retrieve_predicate(uid)
    if not existing:
        abort(BAD_REQUEST, f"Predicate of id {uid} not found in repo.")
    removed = remove_predicate(uid)
    if not removed:
        abort(INTERNAL_SERVER_ERROR, f"Unexpected error while removing predicate {existing.name}.")
    return resp_ok({})


@predicate_bp.route("/enable/<string:id>", methods=["GET"])
def enable(id):
    uid = UUID(id)
    existing = retrieve_predicate(uid)
    if not existing:
        abort(BAD_REQUEST, f"Predicate of id {uid} not managed by tome repo.")
    enabled = enable_predicate(uid)
    if not enabled:
        abort(INTERNAL_SERVER_ERROR, f"Unexpected error while enabling predicate {existing.name}.")
    return resp_ok({})


@predicate_bp.route("/disable/<string:id>", methods=["GET"])
def disable(id):
    uid = UUID(id)
    existing = retrieve_predicate(uid)
    if not existing:
        abort(BAD_REQUEST, f"Predicate of id {uid} not managed by tome repo.")
    disabled = disable_predicate(uid)
    if not disabled:
        abort(INTERNAL_SERVER_ERROR, f"Unexpected error while disabling predicate {existing.name}.")
    return resp_ok({})
