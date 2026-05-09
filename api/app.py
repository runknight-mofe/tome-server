"""
Aether Mesh Management API
Main application factory and configuration
"""

from flask import Flask, request, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
import logging
import uuid
import os
from functools import wraps

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment ('development', 'testing', 'production')
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'development':
        app.config.from_object('config.DevelopmentConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)
    
    # Register request/response middleware
    register_middleware(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database context for initialization
    with app.app_context():
        # Initialize database tables (in production, use Alembic migrations)
        db.create_all()
        logger.info(f"Database initialized ({config_name})")
    
    return app


def register_middleware(app):
    """Register request/response middleware for logging and telemetry"""
    
    @app.before_request
    def before_request():
        """Before request hook: assign request ID, start timing"""
        g.request_id = str(uuid.uuid4())
        g.start_time = datetime.utcnow()
        
        # Extract mesh_id if present in URL
        g.mesh_id = request.args.get('mesh_id') or \
                   (request.path.split('/meshes/')[1].split('/')[0] 
                    if '/meshes/' in request.path else None)
        
        logger.debug(
            f"[{g.request_id}] {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
    
    @app.after_request
    def after_request(response):
        """After request hook: log response, emit telemetry"""
        if hasattr(g, 'start_time'):
            duration_ms = int(
                (datetime.utcnow() - g.start_time).total_seconds() * 1000
            )
            
            # Log response
            logger.info(
                f"[{g.request_id}] {request.method} {request.path} "
                f"-> {response.status_code} ({duration_ms}ms)"
            )
            
            # Emit telemetry event
            try:
                emit_telemetry_event({
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'aether_api',
                    'level': 'info' if 200 <= response.status_code < 400 else 'warn',
                    'labels': {
                        'mesh_id': g.mesh_id,
                        'method': request.method,
                        'path': request.path,
                        'status_code': str(response.status_code),
                    },
                    'fields': {
                        'request_id': g.request_id,
                        'duration_ms': duration_ms,
                        'ip': request.remote_addr,
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to emit telemetry: {e}")
        
        return response


def register_blueprints(app):
    """Register API blueprints"""
    from api.routes.meshes import mesh_bp
    from api.routes.nodes import nodes_bp
    from api.routes.predicates import predicates_bp
    from api.routes.events import events_bp
    from api.routes.health import health_bp
    from api.routes.telemetry import telemetry_bp
    
    app.register_blueprint(mesh_bp, url_prefix='/api/v1/meshes')
    app.register_blueprint(nodes_bp, url_prefix='/api/v1/meshes')
    app.register_blueprint(predicates_bp, url_prefix='/api/v1/meshes')
    app.register_blueprint(events_bp, url_prefix='/api/v1/meshes')
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(telemetry_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error),
            'request_id': g.get('request_id')
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'request_id': g.get('request_id')
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'request_id': g.get('request_id')
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': f"Resource not found: {request.path}",
            'request_id': g.get('request_id')
        }), 404
    
    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'error': 'Conflict',
            'message': str(error),
            'request_id': g.get('request_id')
        }), 409
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded',
            'request_id': g.get('request_id')
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'request_id': g.get('request_id')
        }), 500


def emit_telemetry_event(event):
    """
    Emit a telemetry event to Loki
    
    Args:
        event: Dictionary with 'timestamp', 'source', 'level', 'labels', 'fields'
    """
    import requests
    import json
    
    loki_url = os.getenv('LOKI_URL', 'http://loki:3100')
    
    # Transform event to Loki format
    stream_labels = {
        k: str(v) for k, v in event.get('labels', {}).items() 
        if v is not None
    }
    stream_labels['source'] = event.get('source', 'unknown')
    stream_labels['level'] = event.get('level', 'info')
    
    timestamp_ns = int(
        datetime.fromisoformat(event['timestamp']).timestamp() * 1e9
    )
    
    payload = {
        'streams': [{
            'stream': stream_labels,
            'values': [
                [str(timestamp_ns), json.dumps(event.get('fields', {}))]
            ]
        }]
    }
    
    try:
        requests.post(
            f"{loki_url}/loki/api/v1/push",
            json=payload,
            timeout=2
        )
    except Exception as e:
        logger.warning(f"Loki push failed: {e}")


# Custom decorators for authorization

def require_admin(f):
    """Decorator: Require admin access to mesh"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has admin token for the mesh
        mesh_id = kwargs.get('mesh_id') or request.args.get('mesh_id')
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization token'}), 401
        
        token = auth_header.split(' ')[1]
        
        # TODO: Validate token against admin_tokens table
        # For now, accept any token (implement JWT verification)
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_mesh_access(f):
    """Decorator: Require access to specific mesh"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        mesh_id = kwargs.get('mesh_id') or request.args.get('mesh_id')
        
        if not mesh_id:
            return jsonify({'error': 'mesh_id required'}), 400
        
        from api.models import Mesh
        mesh = Mesh.query.filter_by(id=mesh_id).first()
        
        if not mesh:
            return jsonify({'error': 'Mesh not found'}), 404
        
        g.mesh = mesh
        return f(*args, **kwargs)
    
    return decorated_function


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
