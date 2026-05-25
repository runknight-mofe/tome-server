import logging
from flask import Blueprint, jsonify, request
import requests

from com.aether.tome.api.tome_config import config
from com.aether.tome.api.tome_server import forward_to_auth

logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

user_bp = Blueprint('user', __name__)

@user_bp.route("/user")
def get_user():
    try:
        # Forward authentication request to the client auth api endpoint
        url = f"{config.auth_api_url}/auth/user"
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}
        resp = requests.get(url, headers=headers, cookies=request.cookies)

        json_data = {}
        if resp.status_code == 200:
            # Client auth indicates successful auth attempt
            user = resp.json()
            if user and user.get("username"):
                # User successfully authenticated to backend identity provider
                json_data = user
            else:
                # Received a 200 code, but user data not included in result
                json_data = { "authenticated": False }
        else:
            json_data = { "authenticated": False }

        # Package the user data
        response = jsonify(json_data)
        response.headers["Connection"] = "keep-alive"
        response.headers["Content-Length"] = str(len(response.get_data()))
        return response
    except Exception as e:
        response = jsonify({ "authenticated": False })
        response.headers["Connection"] = "keep-alive"
        return response
    
@user_bp.route("/logout", methods=["POST"])
def logout():
    return forward_to_auth("/auth/logout", method="POST")

@user_bp.route("/redirect")
def redirect():
    next_url = request.args.get("next", "/")
    return forward_to_auth(f"/auth/redirect?next={next_url}")