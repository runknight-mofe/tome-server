"""
Flask Configuration for Aether Mesh Management API
Settings for development, testing, and production environments
"""

import os
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # API
    API_TITLE = 'Aether Mesh Management API'
    API_VERSION = '1.0.0'
    API_DESCRIPTION = 'REST API for managing UWB mesh topologies'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Telemetry
    LOKI_URL = os.getenv('LOKI_URL', 'http://loki:3100')
    TELEMETRY_ENABLED = os.getenv('TELEMETRY_ENABLED', 'true').lower() == 'true'
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Mesh defaults
    MESH_HISTORY_RETENTION_DAYS = int(os.getenv('MESH_HISTORY_RETENTION_DAYS', '30'))
    MESH_SNAPSHOT_INTERVAL_SECONDS = int(os.getenv('MESH_SNAPSHOT_INTERVAL_SECONDS', '300'))
    MAX_NODES_PER_MESH = int(os.getenv('MAX_NODES_PER_MESH', '100'))
    MAX_PREDICATES_PER_MESH = int(os.getenv('MAX_PREDICATES_PER_MESH', '50'))
    
    # Gateway routing
    GATEWAY_TIMEOUT_SECONDS = int(os.getenv('GATEWAY_TIMEOUT_SECONDS', '30'))
    GATEWAY_RETRY_ATTEMPTS = int(os.getenv('GATEWAY_RETRY_ATTEMPTS', '3'))
    
    # UWB/MOFE integration
    MOFE_RUNTIME_URL = os.getenv('MOFE_RUNTIME_URL', 'http://localhost:8080')
    ENABLE_MOFE_SYNC = os.getenv('ENABLE_MOFE_SYNC', 'false').lower() == 'true'


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database - local PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://aether_app:password@localhost:5432/aether_mesh_dev'
    )
    
    # Detailed error messages
    PROPAGATE_EXCEPTIONS = True
    
    # Telemetry
    TELEMETRY_ENABLED = True
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # In-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Disable telemetry for tests
    TELEMETRY_ENABLED = False
    
    # JWT - shorter expiry for tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database - managed service or replicated
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://aether_app:password@postgres-primary:5432/aether_mesh_prod'
    )
    
    # Production database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 40,
    }
    
    # Strict error handling
    PROPAGATE_EXCEPTIONS = False
    
    # Telemetry - required in production
    TELEMETRY_ENABLED = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Caching
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate limiting - stricter in production
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per day, 20 per hour"


def get_config(env=None):
    """Get configuration object for the given environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return configs.get(env, DevelopmentConfig)
