import logging
import debugpy
from flask import Flask
from flask_cors import CORS

from app.config import config
if config.debug:
    # Optional debug mode
    debugpy.listen((config.debug_host, config.debug_port))


logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False


app = Flask(__name__)

origins = config.cors_origins.split(",")
# CORS(user_bp, supports_credentials=True, origins=origins)
# CORS(puzzle_bp, supports_credentials=True, origins=origins)

# app.register_blueprint(user_bp)
# app.register_blueprint(puzzle_bp)

CORS(app, supports_credentials=True, origins=origins)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.api_port)