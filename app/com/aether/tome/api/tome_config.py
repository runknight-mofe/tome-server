from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Type

from com.runknight.model.base_model import BaseDataModel


@dataclass
class TomeConfig(BaseDataModel):

    LOG_LEVEL_DEBUG             = 'DEBUG'
    LOG_LEVEL_INFO              = 'INFO'
    LOG_LEVEL_WARNING           = 'WARNING'
    LOG_LEVEL_ERROR             = 'ERROR'
    LOG_LEVEL_CRITICAL          = 'CRITICAL'
    LOG_LEVELS = {
        LOG_LEVEL_DEBUG : logging.DEBUG,
        LOG_LEVEL_INFO : logging.INFO,
        LOG_LEVEL_WARNING : logging.WARNING,
        LOG_LEVEL_ERROR : logging.ERROR,
        LOG_LEVEL_CRITICAL : logging.CRITICAL
    }

    ENV_DEVELOPMENT             = "development"
    ENV_TESTING                 = "testing"
    ENV_PRODUCTION              = "production"
    ENVIRONMENTS = [ ENV_DEVELOPMENT, ENV_TESTING, ENV_PRODUCTION ]


    # -----------------------------------------------------------
    # Settings
    # -----------------------------------------------------------

    # Web Accessibility
    TOME_API_URL                    = "tome-api-url"
    TOME_API_PORT                   = "tome-api-port"
    SECOND                          = "second"
    MINUTE                          = "minute"
    HOUR                            = "hour"
    DAY                             = "day"
    WEEK                            = "week"
    RATE_LIMITING_ENABLE            = "rate-limiting-enabled"
    RATE_LIMITING_DEFAULTS          = "rate-limiting-defaults"
    TOME_API_CORS_ORIGINS           = "api-cors-origins"
    TOME_SESSION_COOKIE_NAME        = "session-cookie-name"


    # -----------------------------------------------------------
    # Startup 
    # -----------------------------------------------------------

    # Backend DB connection params
    TOME_DB                         = "tome-db"
    URL                             = "url"
    PORT                            = "port"
    NAME                            = "name"
    USER                            = "user"
    PASS                            = "pass"

    # API Log and Debug
    ENVIRONMENT                     = "environment"
    DEBUG_MODE_ENABLE               = "debug-mode-enable"
    DEBUG_MODE_HOST                 = "debug-mode-host"
    DEBUG_MODE_PORT                 = "debug-mode-port"
    LOG_LEVEL                       = "log-level"

    # Web Client auth endpoint
    AUTH_API                        = "auth-api"

    # -----------------------------------------------------------
    # Web App Settings
    # -----------------------------------------------------------



    # -----------------------------------------------------------
    # Base Data Model Declarations
    # -----------------------------------------------------------
    EXPECTED_FIELDS = {
        AUTH_API                    : dict,
        TOME_API_URL                : str,
        TOME_API_PORT               : int,
        TOME_DB                     : dict
    }

    OPTIONAL_FIELDS = {
        ENVIRONMENT                 : str,
        RATE_LIMITING_ENABLE        : bool,
        RATE_LIMITING_DEFAULTS      : dict,
        TOME_API_CORS_ORIGINS       : str,
        DEBUG_MODE_ENABLE           : bool,
        DEBUG_MODE_HOST             : str,
        DEBUG_MODE_PORT             : int,
        LOG_LEVEL                   : str,
        TOME_SESSION_COOKIE_NAME    : str,
    }

    # Default values for optional params
    DEFAULT_VALUES = {
        ENVIRONMENT                 : ENV_DEVELOPMENT,
        RATE_LIMITING_ENABLE : False,
        RATE_LIMITING_DEFAULTS        : {
            SECOND : None,
            MINUTE : None,
            HOUR : None,
            DAY : None,
            WEEK : None,
        },
        DEBUG_MODE_ENABLE           : False,
        DEBUG_MODE_HOST             : "0.0.0.0",
        DEBUG_MODE_PORT             : 5678,
        LOG_LEVEL                   : LOG_LEVEL_ERROR,
        TOME_API_CORS_ORIGINS       : "*",
        TOME_SESSION_COOKIE_NAME    : "session",
    }

    FIELD_TYPES = {
        TOME_API_URL                :str,
        TOME_API_PORT               :int,
        TOME_DB                     :dict
    }

    @staticmethod
    def get_default_values():
        return TomeConfig.DEFAULT_VALUES
    
    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return TomeConfig.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return TomeConfig.OPTIONAL_FIELDS


    # -------------------------------------------------------------------------
    # Initialize
    # -------------------------------------------------------------------------
    def __init__(self, params):

        super().__init__(params)

        # ---------------------------------------------------------------------
        # API Settings
        # ---------------------------------------------------------------------
        self.api_url                        :str        = self._data[TomeConfig.TOME_API_URL]
        """URL at which the api will run"""
        self.api_port                       :int        = self._data[TomeConfig.TOME_API_PORT]
        """port on which the api will run"""
        self.api_access_limits_enabled      :bool       = self._data[TomeConfig.RATE_LIMITING_ENABLE]
        """Flag for enabling rate limiting on API access"""
        self.api_access_limits_per_second   :int | None = self._data[TomeConfig.RATE_LIMITING_DEFAULTS][TomeConfig.SECOND]
        """Default per SECOND restriction on API access frequency per remote endpoint"""
        self.api_access_limits_per_minute   :int | None = self._data[TomeConfig.RATE_LIMITING_DEFAULTS][TomeConfig.MINUTE]
        """Default per MINUTE restriction on API access frequency per remote endpoint"""
        self.api_access_limits_per_hour     :int | None = self._data[TomeConfig.RATE_LIMITING_DEFAULTS][TomeConfig.HOUR]
        """Default HOURLY restriction on API access frequency per remote endpoint"""
        self.api_access_limits_per_day      :int | None = self._data[TomeConfig.RATE_LIMITING_DEFAULTS][TomeConfig.DAY]
        """Default DAILY restriction on API access frequency per remote endpoint"""
        self.api_access_limits_per_week     :int | None = self._data[TomeConfig.RATE_LIMITING_DEFAULTS][TomeConfig.WEEK]
        """Default WEEKLY restriction on API access frequency per remote endpoint"""
        self.api_cors_origins               :str        = self._data[TomeConfig.TOME_API_CORS_ORIGINS]
        """Cross origin security origins allowed for app api"""
        self.session_cookie_name            :str        = self._data[TomeConfig.TOME_SESSION_COOKIE_NAME]
        """Name of the session cookie"""

        # ---------------------------------------------------------------------
        # Debug & Logging
        # ---------------------------------------------------------------------
        self.environment                    :str        = self._data[TomeConfig.ENVIRONMENT]
        """Operation mode"""
        self.debug_mode_enable             :bool        = self._data[TomeConfig.DEBUG_MODE_ENABLE]
        """Flag for enabling remote debugging"""
        self.debug_mode_host               :str         = self._data[TomeConfig.DEBUG_MODE_HOST]
        """Debugging host"""
        self.debug_mode_port               :int         = self._data[TomeConfig.DEBUG_MODE_PORT]
        """Remote debugging port"""
        self.log_level                     :int         = TomeConfig.LOG_LEVELS[self._data[TomeConfig.LOG_LEVEL]]
        """Logging severity level"""


        # ---------------------------------------------------------------------
        # Database
        # ---------------------------------------------------------------------
        self.db_host                       :str         = self._data[TomeConfig.TOME_DB][TomeConfig.URL]
        """hostname for the wordgame db"""
        self.db_port                       :int         = self._data[TomeConfig.TOME_DB][TomeConfig.PORT]
        """port number for the wordgame db host"""
        self.db_name                       :str         = self._data[TomeConfig.TOME_DB][TomeConfig.NAME]
        """database name for wordgame data"""
        self.db_pass                       :str         = self._data[TomeConfig.TOME_DB][TomeConfig.PASS]
        """password for the wordgame db user"""
        self.db_user                       :str         = self._data[TomeConfig.TOME_DB][TomeConfig.USER]
        """user for the wordgame db"""


        # ---------------------------------------------------------------------
        # Web Auth
        # ---------------------------------------------------------------------
        self.auth_api_url                  :str         = self._data[TomeConfig.AUTH_API][TomeConfig.URL]
        """Full URL for the user authentication endpoint"""
        self.auth_api_port                 :int         = self._data[TomeConfig.AUTH_API][TomeConfig.PORT]
        """Port at which the auth api service is running"""

# Load configuration
config: TomeConfig
script_dir = Path(__file__).parent
with open(f"{script_dir}/config.json", 'r') as f:
    config = TomeConfig.from_json(f.read())
if not config:
    raise RuntimeError(f"Failed to parse config from required config.json", e)
