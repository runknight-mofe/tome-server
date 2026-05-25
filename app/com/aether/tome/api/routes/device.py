from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR
import logging
from uuid import UUID

from flask import Blueprint, abort, request
from com.aether.tome.api.schema.device_schema import device_create_req_schema
from com.aether.tome.api.service.device import disable_device, enable_device, register_device, retrieve_device, unregister_device
from com.aether.tome.api.tome_server import resp_ok
from com.aether.tome.api.tome_config import config

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

device_bp = Blueprint('device', __name__)

#----------------------------------------------------------------------------
# get   - Retrieve a device by ID
# [GET] - id : str
#----------------------------------------------------------------------------
@device_bp.route("/get/<string:id>", methods=["GET"])
def get_device(id):
    uid = UUID(id)
    device = retrieve_device(uid)
    if device:
        return resp_ok({"device":device.to_dict()})
    return resp_ok({})

#----------------------------------------------------------------------------
# register  - Register a device to tome database
# [POST]    - Device
#----------------------------------------------------------------------------
@device_bp.route("/register", methods=["POST"])
def register():

    device = device_create_req_schema.load_data(request.get_json())
    if not device:
        abort(BAD_REQUEST, "Unable to validate device")
    registered = register_device(device)
    if not registered:
        abort(INTERNAL_SERVER_ERROR, f"Unable to add device {device.name} at this time due to server error.")
    return resp_ok({"device":registered.to_dict()})


#----------------------------------------------------------------------------
# unregister    - Unregister a device from the tome database
# [GET]         - id : str
#----------------------------------------------------------------------------
@device_bp.route("/unregister/<string:id>", methods=["GET"])
def unregister(id):
    uid = UUID(id)

    existing = retrieve_device(uid)
    if not existing:
        abort(BAD_REQUEST, f"Device of id {uid} not found in repo.")
    removed = unregister_device(uid)
    if not removed:
        abort(INTERNAL_SERVER_ERROR, f"Unpexected error while removing device {existing.name}.")
    return resp_ok({})


#----------------------------------------------------------------------------
# enable    - Enables a disabled device; by ID
# [GET]     - id : str
#----------------------------------------------------------------------------
@device_bp.route("/enable/<string:id>", methods=["GET"])
def enable(id):
    uid = UUID(id)

    existing = retrieve_device(uid)
    if not existing:
        abort(BAD_REQUEST, f"Device of id {uid} not managed by tome repo.")
    enabled = enable_device(uid)
    if not enabled:
        abort(INTERNAL_SERVER_ERROR, f"Unpexected error while enabling device {existing.name}.")
    return resp_ok({})


#----------------------------------------------------------------------------
# disable   - Enables a disabled device; by ID
# [GET]     - id : str
#----------------------------------------------------------------------------
@device_bp.route("/disable/<string:id>", methods=["GET"])
def disable(id):
    uid = UUID(id)

    existing = retrieve_device(uid)
    if not existing:
        abort(BAD_REQUEST, f"Device of id {uid} not managed by tome repo.")
    disabled = disable_device(uid)
    if not disabled:
        abort(INTERNAL_SERVER_ERROR, f"Unpexected error while disabling device {existing.name}.")
    return resp_ok({})
