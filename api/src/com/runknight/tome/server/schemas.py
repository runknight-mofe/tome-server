"""
Aether Mesh Management API - Marshmallow Schemas
Validation and serialization schemas for API contracts
"""

from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from datetime import datetime


# ============================================================================
# VECTOR & COORDINATE SCHEMAS
# ============================================================================

class Vector3DSchema(Schema):
    """3D Vector (x, y, z)"""
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    z = fields.Float(required=True)


class QuaternionSchema(Schema):
    """Quaternion orientation (qx, qy, qz, qw)"""
    qx = fields.Float(required=True)
    qy = fields.Float(required=True)
    qz = fields.Float(required=True)
    qw = fields.Float(required=True)


# ============================================================================
# NODE SCHEMAS
# ============================================================================

class NodeCreateSchema(Schema):
    """Schema for creating a new node"""
    id = fields.String(required=True, validate=validate.Length(min=1, max=255))
    type = fields.String(
        required=True,
        validate=validate.OneOf(['anchor', 'client']),
        error_messages={'validate': 'type must be "anchor" or "client"'}
    )
    position = fields.Nested(Vector3DSchema, required=False)
    orientation = fields.Nested(QuaternionSchema, required=False, dump_default={})
    is_emulated = fields.Boolean(required=False, dump_default=False)
    metadata = fields.Dict(required=False)
    
    @post_load
    def create_node(self, data, **kwargs):
        """Post-process loaded data"""
        if 'position' not in data:
            data['position'] = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        if 'orientation' not in data:
            data['orientation'] = {'qx': 0.0, 'qy': 0.0, 'qz': 0.0, 'qw': 1.0}
        return data


class NodeUpdateSchema(Schema):
    """Schema for updating an existing node"""
    position = fields.Nested(Vector3DSchema, required=False)
    orientation = fields.Nested(QuaternionSchema, required=False)
    acceleration = fields.Nested(Vector3DSchema, required=False)
    status = fields.String(
        required=False,
        validate=validate.OneOf(['online', 'offline', 'degraded', 'error'])
    )
    signal_quality = fields.Float(required=False, validate=validate.Range(min=0, max=1))
    is_emulated = fields.Boolean(required=False)
    metadata = fields.Dict(required=False)


class NodeSchema(Schema):
    """Schema for node representation"""
    id = fields.String(required=True)
    mesh_id = fields.UUID(required=True)
    type = fields.String(required=True)
    role = fields.String(required=False)
    position = fields.Nested(Vector3DSchema)
    orientation = fields.Nested(QuaternionSchema)
    acceleration = fields.Nested(Vector3DSchema)
    status = fields.String(required=True)
    signal_quality = fields.Float()
    rssi = fields.Float()
    is_admin = fields.Boolean()
    is_root = fields.Boolean()
    is_emulated = fields.Boolean()
    last_seen = fields.DateTime()
    joined_at = fields.DateTime()
    metadata = fields.Dict()


# ============================================================================
# PREDICATE SCHEMAS
# ============================================================================

class PredicateCreateSchema(Schema):
    """Schema for creating a new predicate"""
    id = fields.String(required=True, validate=validate.Length(min=1, max=255))
    type = fields.String(
        required=True,
        validate=validate.OneOf(['point', 'line', 'box', 'circle', 'sphere', 'cylinder']),
        error_messages={'validate': 'type must be one of: point, line, box, circle, sphere, cylinder'}
    )
    position = fields.Nested(Vector3DSchema, required=True)
    geometry = fields.Dict(required=True)  # Type-specific geometry
    hysteresis = fields.Float(required=False, dump_default=0.05, validate=validate.Range(min=0))
    event_type = fields.String(required=False)
    enabled = fields.Boolean(required=False, dump_default=True)
    
    @post_load
    def validate_geometry(self, data, **kwargs):
        """Validate geometry based on predicate type"""
        predicate_type = data.get('type')
        geometry = data.get('geometry', {})
        
        # Validation rules for each type
        validation_rules = {
            'point': [],  # No special requirements
            'line': ['end_x', 'end_y', 'end_z'],
            'box': ['width', 'height', 'depth'],
            'circle': ['radius'],
            'sphere': ['radius'],
            'cylinder': ['radius', 'height'],
        }
        
        required_fields = validation_rules.get(predicate_type, [])
        for field in required_fields:
            if field not in geometry:
                raise ValidationError(
                    f"geometry.{field} required for type '{predicate_type}'"
                )
        
        return data


class PredicateUpdateSchema(Schema):
    """Schema for updating an existing predicate"""
    position = fields.Nested(Vector3DSchema, required=False)
    geometry = fields.Dict(required=False)
    hysteresis = fields.Float(required=False, validate=validate.Range(min=0))
    event_type = fields.String(required=False)
    enabled = fields.Boolean(required=False)


class PredicateSchema(Schema):
    """Schema for predicate representation"""
    id = fields.String(required=True)
    mesh_id = fields.UUID(required=True)
    type = fields.String(required=True)
    position = fields.Nested(Vector3DSchema)
    geometry = fields.Dict()
    hysteresis = fields.Float()
    event_type = fields.String()
    event_id = fields.String()
    enabled = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# ============================================================================
# EVENT SCHEMAS
# ============================================================================

class MeshEventSchema(Schema):
    """Schema for mesh event representation"""
    id = fields.UUID(required=True)
    mesh_id = fields.UUID(required=True)
    source = fields.String(required=True)
    event_type = fields.String(required=True)
    severity = fields.String()
    predicate_id = fields.String()
    node_id = fields.String()
    triggered_by_node_id = fields.String()
    event_data = fields.Dict()
    message = fields.String()
    timestamp = fields.DateTime()
    duration_ms = fields.Integer()
    request_id = fields.String()


class MeshEventQuerySchema(Schema):
    """Schema for querying mesh events"""
    event_type = fields.String(required=False)
    node_id = fields.String(required=False)
    predicate_id = fields.String(required=False)
    severity = fields.String(
        required=False,
        validate=validate.OneOf(['debug', 'info', 'warn', 'error', 'critical'])
    )
    limit = fields.Integer(required=False, dump_default=100, validate=validate.Range(min=1, max=1000))
    offset = fields.Integer(required=False, dump_default=0, validate=validate.Range(min=0))


# ============================================================================
# MESH SCHEMAS
# ============================================================================

class MeshCreateSchema(Schema):
    """Schema for creating a new mesh"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(required=False)
    metadata = fields.Dict(required=False)


class MeshUpdateSchema(Schema):
    """Schema for updating an existing mesh"""
    name = fields.String(required=False, validate=validate.Length(min=1, max=255))
    description = fields.String(required=False)
    status = fields.String(
        required=False,
        validate=validate.OneOf(['active', 'archived', 'deleted', 'suspended'])
    )
    metadata = fields.Dict(required=False)


class MeshSchema(Schema):
    """Schema for mesh representation"""
    id = fields.UUID(required=True)
    name = fields.String(required=True)
    description = fields.String()
    status = fields.String()
    operating_mode = fields.String()
    root_node_id = fields.String()
    anchor_count = fields.Integer()
    client_count = fields.Integer()
    online_count = fields.Integer()
    offline_count = fields.Integer()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    nodes = fields.List(fields.Nested(NodeSchema), required=False)
    predicates = fields.List(fields.Nested(PredicateSchema), required=False)


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class AdminTokenCreateSchema(Schema):
    """Schema for creating admin token"""
    node_id = fields.String(required=True)
    expires_in_days = fields.Integer(required=False, dump_default=30)


class AdminTokenSchema(Schema):
    """Schema for admin token representation"""
    id = fields.UUID()
    mesh_id = fields.UUID()
    node_id = fields.String()
    token_type = fields.String()
    scope = fields.String()
    created_at = fields.DateTime()
    expires_at = fields.DateTime()
    is_active = fields.Boolean()
    is_expired = fields.Boolean()


# ============================================================================
# HEALTH & DIAGNOSTICS SCHEMAS
# ============================================================================

class MeshHealthSchema(Schema):
    """Schema for mesh health information"""
    mesh_id = fields.UUID()
    status = fields.String()
    anchor_count = fields.Integer()
    client_count = fields.Integer()
    online_count = fields.Integer()
    offline_count = fields.Integer()
    average_signal_quality = fields.Float()
    gdop = fields.Float()
    last_event_timestamp = fields.DateTime()
    last_event_type = fields.String()
    uptime_seconds = fields.Integer()


# ============================================================================
# TELEMETRY SCHEMAS
# ============================================================================

class TelemetryEventSchema(Schema):
    """Schema for telemetry event"""
    timestamp = fields.DateTime(required=True)
    source = fields.String(required=True)
    level = fields.String(
        required=True,
        validate=validate.OneOf(['debug', 'info', 'warn', 'error', 'critical'])
    )
    labels = fields.Dict(required=True)
    fields = fields.Dict(required=True)


# ============================================================================
# SCHEMA INSTANCES (for export)
# ============================================================================

mesh_create_schema = MeshCreateSchema()
mesh_update_schema = MeshUpdateSchema()
mesh_schema = MeshSchema()
meshes_schema = MeshSchema(many=True)

node_create_schema = NodeCreateSchema()
node_update_schema = NodeUpdateSchema()
node_schema = NodeSchema()
nodes_schema = NodeSchema(many=True)

predicate_create_schema = PredicateCreateSchema()
predicate_update_schema = PredicateUpdateSchema()
predicate_schema = PredicateSchema()
predicates_schema = PredicateSchema(many=True)

mesh_event_schema = MeshEventSchema()
mesh_events_schema = MeshEventSchema(many=True)
mesh_event_query_schema = MeshEventQuerySchema()

admin_token_create_schema = AdminTokenCreateSchema()
admin_token_schema = AdminTokenSchema()
admin_tokens_schema = AdminTokenSchema(many=True)

mesh_health_schema = MeshHealthSchema()

telemetry_event_schema = TelemetryEventSchema()
telemetry_events_schema = TelemetryEventSchema(many=True)
