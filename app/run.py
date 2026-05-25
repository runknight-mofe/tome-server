import logging
import debugpy

from com.aether.tome.api.tome_server import create_app
from com.aether.tome.api.tome_config import config

if config.debug_mode_enable:
    # Optional debug mode
    debugpy.listen((config.debug_mode_host, config.debug_mode_port))


logging.basicConfig(level=config.log_level, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host=config.api_url, port=config.api_port)