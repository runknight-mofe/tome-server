"""
Aether Mesh Management API - Data Models
SQLAlchemy models for all database entities
"""

from datetime import datetime, timedelta
from uuid import uuid4
import json
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app import db


class Mesh(db.Model):
    """Mesh entity - represents a complete UWB mesh topology"""
    __tablename__ = 'meshes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    status = db.Column(
        db.String(50),
        nullable=False,
        default='active',
        server_default='active'
    )
    root_node_id = db.Column(db.String(255))
    operating_mode = db.Column(db.String(50), default='unknown')
    coordinate_frame_metadata = db.Column(JSONB)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    created_by_node_id = db.Column(db.String(255))
    
    # Relationships
    nodes = db.relationship('Node', cascade='all, delete-orphan', back_populates='mesh')
    predicates = db.relationship('Predicate', cascade='all, delete-orphan', back_populates='mesh')
    events = db.relationship('MeshEvent', cascade='all, delete-orphan', back_populates='mesh')
    admin_tokens = db.relationship('AdminToken', cascade='all, delete-orphan', back_populates='mesh')
    snapshots = db.relationship('MeshStateSnapshot', cascade='all, delete-orphan', back_populates='mesh')
    health_metrics = db.relationship('MeshHealthMetric', cascade='all, delete-orphan', back_populates='mesh')
    
    def to_dict(self, include_children=False):
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'operating_mode': self.operating_mode,
            'root_node_id': self.root_node_id,
            'anchor_count': len([n for n in self.nodes if n.type == 'anchor']),
            'client_count': len([n for n in self.nodes if n.type == 'client']),
            'online_count': len([n for n in self.nodes if n.status == 'online']),
            'offline_count': len([n for n in self.nodes if n.status == 'offline']),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        
        if include_children:
            data['nodes'] = [n.to_dict() for n in self.nodes]
            data['predicates'] = [p.to_dict() for p in self.predicates]
        
        return data


class Node(db.Model):
    """Node entity - represents a UWB device (anchor or client)"""
    __tablename__ = 'nodes'
    __table_args__ = (
        db.PrimaryKeyConstraint('mesh_id', 'id'),
    )
    
    id = db.Column(db.String(255), primary_key=True)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'anchor' or 'client'
    role = db.Column(db.String(50), default='member')  # member, gateway, admin, root
    
    # Position (cartesian coordinates in local frame)
    position_x = db.Column(db.Float)
    position_y = db.Column(db.Float)
    position_z = db.Column(db.Float)
    
    # Orientation (quaternion)
    orientation_qx = db.Column(db.Float, default=0.0)
    orientation_qy = db.Column(db.Float, default=0.0)
    orientation_qz = db.Column(db.Float, default=0.0)
    orientation_qw = db.Column(db.Float, default=1.0)
    
    # Acceleration (m/s^2)
    accel_x = db.Column(db.Float, default=0.0)
    accel_y = db.Column(db.Float, default=0.0)
    accel_z = db.Column(db.Float, default=0.0)
    
    # Health & communication
    status = db.Column(db.String(50), default='offline')  # online, offline, degraded, error
    signal_quality = db.Column(db.Float, default=0.0)
    rssi = db.Column(db.Float, default=-120.0)
    
    # Metadata
    is_admin = db.Column(db.Boolean, default=False)
    is_root = db.Column(db.Boolean, default=False)
    is_emulated = db.Column(db.Boolean, default=False)
    
    # Timestamps
    last_seen = db.Column(db.DateTime)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extra metadata
    metadata = db.Column(JSONB)
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='nodes')
    events_triggered = db.relationship(
        'MeshEvent',
        foreign_keys='MeshEvent.triggered_by_node_id'
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'mesh_id': str(self.mesh_id),
            'type': self.type,
            'role': self.role,
            'position': {
                'x': self.position_x,
                'y': self.position_y,
                'z': self.position_z,
            },
            'orientation': {
                'qx': self.orientation_qx,
                'qy': self.orientation_qy,
                'qz': self.orientation_qz,
                'qw': self.orientation_qw,
            },
            'acceleration': {
                'x': self.accel_x,
                'y': self.accel_y,
                'z': self.accel_z,
            },
            'status': self.status,
            'signal_quality': self.signal_quality,
            'rssi': self.rssi,
            'is_admin': self.is_admin,
            'is_root': self.is_root,
            'is_emulated': self.is_emulated,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'joined_at': self.joined_at.isoformat(),
            'metadata': self.metadata,
        }


class Predicate(db.Model):
    """Predicate entity - geometric shape for event detection"""
    __tablename__ = 'predicates'
    __table_args__ = (
        db.PrimaryKeyConstraint('mesh_id', 'id'),
    )
    
    id = db.Column(db.String(255), primary_key=True)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # point, line, box, circle, sphere, cylinder
    
    # Anchor point
    position_x = db.Column(db.Float, nullable=False)
    position_y = db.Column(db.Float, nullable=False)
    position_z = db.Column(db.Float, nullable=False)
    
    # Geometry data
    geometry = db.Column(JSONB, nullable=False)  # Type-specific geometry
    
    # Configuration
    hysteresis = db.Column(db.Float, default=0.05)
    enabled = db.Column(db.Boolean, default=True)
    event_type = db.Column(db.String(100))
    event_id = db.Column(db.String(255))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_node_id = db.Column(db.String(255))
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='predicates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mesh_id': str(self.mesh_id),
            'type': self.type,
            'position': {
                'x': self.position_x,
                'y': self.position_y,
                'z': self.position_z,
            },
            'geometry': self.geometry,
            'hysteresis': self.hysteresis,
            'enabled': self.enabled,
            'event_type': self.event_type,
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class MeshEvent(db.Model):
    """MeshEvent entity - audit trail and event history"""
    __tablename__ = 'mesh_events'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), nullable=False)
    
    source = db.Column(db.String(50), nullable=False)  # user, runtime, system, api
    event_type = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(50), default='info')  # debug, info, warn, error, critical
    
    predicate_id = db.Column(db.String(255))
    node_id = db.Column(db.String(255))
    triggered_by_node_id = db.Column(db.String(255), db.ForeignKey('nodes.id'))
    
    event_data = db.Column(JSONB)
    message = db.Column(db.Text)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    duration_ms = db.Column(db.Integer)
    
    request_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='events')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'mesh_id': str(self.mesh_id),
            'source': self.source,
            'event_type': self.event_type,
            'severity': self.severity,
            'predicate_id': self.predicate_id,
            'node_id': self.node_id,
            'triggered_by_node_id': self.triggered_by_node_id,
            'event_data': self.event_data,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms,
            'request_id': self.request_id,
        }


class AdminToken(db.Model):
    """AdminToken entity - API authentication and authorization"""
    __tablename__ = 'admin_tokens'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), nullable=False)
    node_id = db.Column(db.String(255), nullable=False)
    
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    token_type = db.Column(db.String(50), default='api_key')
    scope = db.Column(db.String(255), default='mesh:admin')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='admin_tokens')
    
    def is_expired(self):
        """Check if token has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'mesh_id': str(self.mesh_id),
            'node_id': self.node_id,
            'token_type': self.token_type,
            'scope': self.scope,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
        }


class MeshStateSnapshot(db.Model):
    """MeshStateSnapshot entity - point-in-time mesh state for recovery"""
    __tablename__ = 'mesh_state_snapshots'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), nullable=False)
    
    nodes_json = db.Column(JSONB, nullable=False)
    predicates_json = db.Column(JSONB, nullable=False)
    frame_data_json = db.Column(JSONB)
    operating_mode = db.Column(db.String(50))
    gdop = db.Column(db.Float)
    anchor_count = db.Column(db.Integer)
    client_count = db.Column(db.Integer)
    
    source = db.Column(db.String(50), default='periodic')  # periodic, manual, recovery
    snapshot_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_node_id = db.Column(db.String(255))
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='snapshots')


class MeshHealthMetric(db.Model):
    """MeshHealthMetric entity - rolling health metrics"""
    __tablename__ = 'mesh_health_metrics'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), nullable=False)
    
    anchor_count = db.Column(db.Integer)
    client_count = db.Column(db.Integer)
    online_node_count = db.Column(db.Integer)
    offline_node_count = db.Column(db.Integer)
    average_signal_quality = db.Column(db.Float)
    
    gdop = db.Column(db.Float)
    position_residual_rms = db.Column(db.Float)
    update_frequency_hz = db.Column(db.Float)
    
    event_count_1min = db.Column(db.Integer, default=0)
    event_count_5min = db.Column(db.Integer, default=0)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    mesh = db.relationship('Mesh', back_populates='health_metrics')


class RangingMeasurement(db.Model):
    """RangingMeasurement entity - historical ranging data"""
    __tablename__ = 'ranging_measurements'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    mesh_id = db.Column(UUID(as_uuid=True), db.ForeignKey('meshes.id'), nullable=False)
    
    anchor_id = db.Column(db.String(255), nullable=False)
    target_id = db.Column(db.String(255), nullable=False)
    
    distance = db.Column(db.Float, nullable=False)
    variance = db.Column(db.Float)
    signal_quality = db.Column(db.Float)
    rssi = db.Column(db.Float)
    nlos = db.Column(db.Boolean, default=False)
    
    azimuth = db.Column(db.Float)
    elevation = db.Column(db.Float)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    measurement_type = db.Column(db.String(50))
    cycle_id = db.Column(db.BigInteger)
