# Aether Mesh Management System - Complete Design & Implementation Plan

## Executive Summary

A thin client system for hands-on mock testing of MOFE (Multi-Observer Fusion Engine) capability set. The system comprises:

1. **Web Client** (React/D3.js) - Interactive mesh visualization and management
2. **Aether API** (Python/Flask) - REST contract for mesh operations and gateway routing
3. **Data Backend** (PostgreSQL) - Mesh metadata and state persistence
4. **Telemetry** (Loki/Grafana) - Real-time monitoring and diagnostics

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WEB CLIENT (React)                          │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Mesh Topology  │  │ Node Manager │  │ Predicate Editor   │    │
│  │   Visualizer    │  │   (Join/Leave)  │ (Geometric Shapes) │    │
│  │   (D3.js)       │  │              │  │                    │    │
│  └─────────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Telemetry Client → Loki (http://loki:3100)                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────┴──────────────────────────────────────────────┐
│                    AETHER API (Python/Flask)                        │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ Mesh API        │  │  Node API    │  │  Predicate API   │     │
│  │ Contracts       │  │  (membership)│  │  (CRUD)          │     │
│  └──────────────────┘  └──────────────┘  └──────────────────┘     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Gateway Router (Admin auth + Routing to Root Anchor)     │      │
│  └──────────────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Telemetry Emitter → Loki                                │      │
│  └──────────────────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ MOFE Runtime / UWB Communication
┌──────────────────────┴──────────────────────────────────────────────┐
│                  MOFE RUNTIME (Admin Node/Root Anchor)              │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ CoordinateFrameManager (Topology, Anchors, Frame State) │      │
│  │ MultiObserverFusionEngine (5-Stage Pipeline)            │      │
│  │ MeshState (Nodes, Predicates, Events)                   │      │
│  └──────────────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Telemetry Emitter (Event/State events to Loki)          │      │
│  └──────────────────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ SQL
┌──────────────────────┴──────────────────────────────────────────────┐
│                    POSTGRESQL (Persistence)                         │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ Mesh Metadata   │  │ Node States  │  │ Predicate Config │     │
│  │ (ID, Name, etc) │  │ (Position,   │  │ (Geometry,       │     │
│  │                  │  │  Type, Roles)│  │  Type, Events)   │     │
│  └──────────────────┘  └──────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘

└─────────────────────────────────────────────────────────────────────┘
│                  MONITORING & DIAGNOSTICS (Grafana)                 │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Topology Health, Per-Node Metrics, Event Timeline        │      │
│  │ Data Source: Loki (http://localhost:3000)               │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Web Client (React/TypeScript + D3.js)

#### 1.1 Core Responsibilities
- **Mesh Visualization**: Real-time D3 rendering of nodes, anchors, clients, predicates
- **Interactive Management**: Node membership, predicate creation/editing
- **Emulated Device Control**: Orientation, acceleration, position manipulation
- **Responsive UI**: Desktop + mobile (portrait/landscape)
- **Telemetry Client**: Push metrics to Loki

#### 1.2 Key Features
- **Topology View**
  - Primary focus: interactive D3 graph
  - Nodes: colored by type (anchor/client)
  - Edges: ranges, signal quality visualization
  - Predicates: geometric shapes overlaid on graph
  - Predicate types: Point, Line, Box, Sphere, Cylinder
  
- **Node Management Panel**
  - Add/remove nodes
  - Set node type (anchor/client)
  - View node properties (position, status, signal quality)
  - For emulated devices: control position, orientation (quaternion), acceleration
  
- **Predicate Editor**
  - Interactive creation: click to place, drag to define
  - Types: Point, Line (2D/3D), Box (2D/3D), Circle/Sphere, Cylinder
  - Drag/resize handles for manipulation
  - Delete, rename, configure hysteresis
  
- **Event Timeline**
  - Scrollable event log
  - Filter by type, node, predicate
  - Time-series visualization
  
- **Responsive Layout**
  - Desktop: 3-column (topology | details | events)
  - Mobile portrait: stacked (topology | details)
  - Mobile landscape: 2-column + collapsible details

#### 1.3 Technical Stack
- **React 18+** with TypeScript
- **D3.js v7+** for graph/visualization
- **Tailwind CSS** for responsive styling
- **Zustand** for state management
- **Vite** for bundling
- **Fetch API** for REST calls to Aether API

#### 1.4 Data Model (Frontend)
```typescript
interface Mesh {
  id: string;
  name: string;
  status: "connected" | "disconnected" | "degraded";
  connectedAt: ISO8601;
  anchorCount: number;
  clientCount: number;
  coordinateFrame: CoordinateFrame;
}

interface Node {
  id: DeviceId;
  type: "anchor" | "client";
  position: Vector3D;
  status: "online" | "offline" | "degraded";
  signalQuality: number; // 0-1
  isAdmin: boolean;
  isRoot: boolean;
  lastSeen: ISO8601;
  
  // For emulated devices:
  emulated?: {
    orientation: Quaternion;
    acceleration: Vector3D;
    controlMode: "manual" | "recording";
  };
}

interface Predicate {
  id: string;
  type: "point" | "line" | "box" | "circle" | "sphere" | "cylinder";
  position: Vector3D;
  properties: {
    // Type-specific properties
    lineEnd?: Vector3D;      // For lines
    width?: number;          // For boxes
    height?: number;         // For boxes
    radius?: number;         // For circles, spheres, cylinders
  };
  hysteresis: number;        // Proximity hysteresis (meters)
  eventId: string;           // Associated event detector ID
}

interface MeshEvent {
  id: string;
  timestamp: ISO8601;
  type: "proximity" | "boundary" | "gesture" | "collision";
  predicateId: string;
  nodeId?: DeviceId;
  data: Record<string, any>;
}
```

---

### 2. Aether API (Python/Flask)

#### 2.1 Core Responsibilities
- **REST Contract**: Well-structured endpoints for mesh operations
- **Authentication**: Admin-only access to API (ROOT anchor by default)
- **Gateway Router**: Proxy requests to root anchor / MOFE runtime
- **Mesh Persistence**: CRUD operations on PostgreSQL
- **Telemetry**: Emit metrics to Loki

#### 2.2 Endpoints

##### Mesh Management
```
GET    /api/v1/meshes                          # List meshes
POST   /api/v1/meshes                          # Create mesh
GET    /api/v1/meshes/{mesh_id}                # Get mesh details
PUT    /api/v1/meshes/{mesh_id}                # Update mesh
DELETE /api/v1/meshes/{mesh_id}                # Delete mesh
POST   /api/v1/meshes/{mesh_id}/join           # Join existing mesh
POST   /api/v1/meshes/{mesh_id}/leave          # Leave mesh
```

##### Node Management
```
GET    /api/v1/meshes/{mesh_id}/nodes          # List nodes in mesh
POST   /api/v1/meshes/{mesh_id}/nodes          # Add node to mesh
GET    /api/v1/meshes/{mesh_id}/nodes/{node_id}  # Get node state
PUT    /api/v1/meshes/{mesh_id}/nodes/{node_id}  # Update node
DELETE /api/v1/meshes/{mesh_id}/nodes/{node_id}  # Remove node
POST   /api/v1/meshes/{mesh_id}/nodes/{node_id}/emulate  # Start emulation
PUT    /api/v1/meshes/{mesh_id}/nodes/{node_id}/position # Update position (emulated)
PUT    /api/v1/meshes/{mesh_id}/nodes/{node_id}/orientation # Update orientation
PUT    /api/v1/meshes/{mesh_id}/nodes/{node_id}/acceleration # Update acceleration
```

##### Predicate Management
```
GET    /api/v1/meshes/{mesh_id}/predicates     # List predicates
POST   /api/v1/meshes/{mesh_id}/predicates     # Create predicate
GET    /api/v1/meshes/{mesh_id}/predicates/{pred_id}  # Get predicate
PUT    /api/v1/meshes/{mesh_id}/predicates/{pred_id}  # Update predicate
DELETE /api/v1/meshes/{mesh_id}/predicates/{pred_id}  # Delete predicate
```

##### Events
```
GET    /api/v1/meshes/{mesh_id}/events         # Stream or list events
GET    /api/v1/meshes/{mesh_id}/events?predicate={id}&node={id}  # Filter
WebSocket /ws/meshes/{mesh_id}/events          # Event stream subscription
```

##### Telemetry
```
POST   /api/v1/telemetry                       # Push telemetry (used internally)
GET    /api/v1/meshes/{mesh_id}/health         # Mesh health summary
```

#### 2.3 Authentication
- **Token-based**: JWT or API Key
- **Scope**: Admin (API access) vs. Regular (node operations)
- **Default**: ROOT anchor node is admin; can authorize other nodes

#### 2.4 Data Models (API)

```python
# Marshmallow schemas for validation/serialization

class VectorSchema(Schema):
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    z = fields.Float(required=True)

class NodeSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True, validate=OneOf(['anchor', 'client']))
    position = fields.Nested(VectorSchema)
    status = fields.String(validate=OneOf(['online', 'offline', 'degraded']))
    signalQuality = fields.Float(validate=Range(min=0, max=1))
    isAdmin = fields.Boolean()
    isRoot = fields.Boolean()
    lastSeen = fields.DateTime()
    emulated = fields.Dict(dump_default=None)  # Emulation state

class PredicateSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True, validate=OneOf([
        'point', 'line', 'box', 'circle', 'sphere', 'cylinder'
    ]))
    position = fields.Nested(VectorSchema, required=True)
    properties = fields.Dict()  # Type-specific
    hysteresis = fields.Float(default=0.05)
    eventId = fields.String()

class MeshEventSchema(Schema):
    id = fields.String(required=True)
    timestamp = fields.DateTime()
    type = fields.String(required=True)
    predicateId = fields.String()
    nodeId = fields.String()
    data = fields.Dict()

class MeshSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    status = fields.String()
    connectedAt = fields.DateTime()
    nodes = fields.List(fields.Nested(NodeSchema))
    predicates = fields.List(fields.Nested(PredicateSchema))
    coordinateFrame = fields.Dict()
```

#### 2.5 Gateway Router Logic

```
API Request (admin-authenticated)
    ↓
Check if operation requires gateway
    ├─ Create/Delete/Update mesh/node/predicate → Persist to DB + route to root
    ├─ Query mesh state → Fetch from root anchor MOFE runtime via internal call
    └─ List/History operations → Query from DB with optional validation
    ↓
If routing to root anchor:
    - Root anchor has MOFE runtime access
    - Sends command via internal protocol (IPC/Socket)
    - Receives response
    ↓
Respond with unified model
```

#### 2.6 Telemetry Schema (to Loki)

```json
{
  "timestamp": "2025-05-09T10:30:45.123Z",
  "source": "aether_api",
  "level": "info",
  "labels": {
    "mesh_id": "mesh-001",
    "component": "api",
    "operation": "create_node"
  },
  "fields": {
    "node_id": "node-42",
    "node_type": "client",
    "request_duration_ms": 124,
    "status": "success"
  }
}
```

---

### 3. Data Backend (PostgreSQL)

#### 3.1 Schema

```sql
-- Meshes
CREATE TABLE meshes (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,  -- Custom metadata
    UNIQUE(name)
);

-- Nodes
CREATE TABLE nodes (
    id VARCHAR(255) NOT NULL,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    type VARCHAR(50) CHECK (type IN ('anchor', 'client')) NOT NULL,
    position_x FLOAT,
    position_y FLOAT,
    position_z FLOAT,
    status VARCHAR(50) DEFAULT 'offline',
    signal_quality FLOAT DEFAULT 0.0,
    is_admin BOOLEAN DEFAULT FALSE,
    is_root BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP,
    emulation_data JSONB,  -- Quaternion, acceleration, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (mesh_id, id)
);

-- Predicates
CREATE TABLE predicates (
    id VARCHAR(255) NOT NULL,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- point, line, box, circle, sphere, cylinder
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    position_z FLOAT NOT NULL,
    properties JSONB,  -- Type-specific geometry
    hysteresis FLOAT DEFAULT 0.05,
    event_id VARCHAR(255),  -- Reference to event detector
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (mesh_id, id)
);

-- Mesh Events (for history/audit)
CREATE TABLE mesh_events (
    id UUID PRIMARY KEY,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    predicate_id VARCHAR(255),
    node_id VARCHAR(255),
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Authentication / Admin Tokens
CREATE TABLE admin_tokens (
    id UUID PRIMARY KEY,
    mesh_id UUID NOT NULL REFERENCES meshes(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    token VARCHAR(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(mesh_id, node_id)
);

-- Indexes for performance
CREATE INDEX idx_nodes_mesh_id ON nodes(mesh_id);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_predicates_mesh_id ON predicates(mesh_id);
CREATE INDEX idx_mesh_events_mesh_id ON mesh_events(mesh_id);
CREATE INDEX idx_mesh_events_timestamp ON mesh_events(timestamp);
```

#### 3.2 Data Retention
- Mesh metadata: Indefinite (or configurable TTL)
- Mesh events: 7-30 days (configurable)
- Telemetry: Handled by Loki (not in PSQL)

---

### 4. Telemetry (Loki Integration)

#### 4.1 Telemetry Sources

**Web Client (TypeScript)**
```typescript
// Emit to Loki via API proxy
interface TelemetryEvent {
  timestamp: ISO8601;
  source: "web_client";
  level: "info" | "warn" | "error";
  labels: {
    mesh_id: string;
    component: "topology" | "node_manager" | "predicate_editor" | "event_timeline";
    action: string;  // e.g., "add_node", "update_predicate"
  };
  fields: {
    node_id?: string;
    predicate_id?: string;
    duration_ms?: number;
    status: "success" | "failure";
    error_message?: string;
  };
}
```

**Aether API (Python)**
```python
# Flask middleware + explicit logging
@app.before_request
def log_request():
    telemetry_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'aether_api',
        'level': 'info',
        'labels': {
            'method': request.method,
            'path': request.path,
            'mesh_id': request.args.get('mesh_id'),
        },
        'fields': {
            'request_id': g.request_id,
            'ip': request.remote_addr,
        }
    }
    emit_to_loki(telemetry_event)

def emit_to_loki(event):
    """Push to Loki (http://loki:3100/loki/api/v1/push)"""
    payload = {
        "streams": [{
            "stream": {k: v for k, v in event['labels'].items() if v},
            "values": [
                [str(int(datetime.fromisoformat(event['timestamp']).timestamp() * 1e9)),
                 json.dumps(event['fields'])]
            ]
        }]
    }
    requests.post("http://loki:3100/loki/api/v1/push", json=payload)
```

**MOFE Runtime (Kotlin → API endpoint)**
```kotlin
// MofeListener integration
override fun onEvent(event: MeshEvent) {
    val telemetryEvent = mapOf(
        "timestamp" to event.timestamp,
        "source" to "mofe_runtime",
        "level" to "info",
        "labels" to mapOf(
            "mesh_id" to mesh.id,
            "component" to "fusion_engine",
            "event_type" to event.type.toString()
        ),
        "fields" to mapOf(
            "node_id" to event.nodeId,
            "predicate_id" to event.predicateId,
            "fused_position" to event.position
        )
    )
    // POST to Aether API /api/v1/telemetry
    apiClient.postTelemetry(telemetryEvent)
}
```

#### 4.2 Grafana Dashboards

**Dashboard 1: Topology Health**
- Mesh status (online/offline/degraded)
- Anchor count, client count
- Average signal quality
- Event frequency (events/min)
- GDOP distribution

**Dashboard 2: Per-Node Metrics**
- Node status timeline
- Signal quality trend
- Position stability (standard deviation)
- IMU data (acceleration, rotation rates)
- Ranging cycle frequency

**Dashboard 3: Event Timeline**
- Event count by type (proximity, boundary, gesture, collision)
- Event lag (timestamp → detection → telemetry)
- Predicate activation frequency

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **PostgreSQL Schema Setup**
   - Create tables, indices
   - Set up migrations (Alembic)

2. **Aether API Skeleton**
   - Flask app, basic routes
   - Marshmallow schemas
   - PostgreSQL connection (SQLAlchemy)

3. **Web Client Setup**
   - React + TypeScript scaffold
   - Zustand store structure
   - Basic UI layout (3-column desktop, responsive mobile)

4. **Telemetry Infrastructure**
   - Loki ingestion wrapper
   - API endpoint for telemetry push

### Phase 2: Mesh Operations (Week 2-3)
1. **Mesh Lifecycle**
   - Create, join, leave, delete
   - Membership management

2. **Node Management**
   - Add/remove nodes
   - Set node type (anchor/client)
   - Emulation mode (position, orientation, acceleration)

3. **Predicate CRUD**
   - Create geometric shapes
   - Update properties
   - Delete predicates

4. **Gateway Router**
   - Admin authentication
   - Routing to root anchor
   - Command queuing if offline

### Phase 3: UI & Visualization (Week 3-4)
1. **D3 Topology Visualization**
   - Node rendering (anchor/client colors)
   - Range edges
   - Predicate overlays

2. **Interactive Manipulation**
   - Drag nodes
   - Resize/rotate predicates
   - Click-to-select

3. **Detail Panels**
   - Node properties
   - Predicate configuration
   - Event timeline

4. **Responsive Design**
   - Mobile portrait/landscape
   - Touch interactions

### Phase 4: Telemetry & Monitoring (Week 4)
1. **Telemetry Emission**
   - Web client → API
   - API → Loki
   - MOFE runtime → Loki (via API)

2. **Grafana Dashboards**
   - Topology health
   - Per-node metrics
   - Event timeline

3. **Testing & Polish**
   - Load testing
   - UX refinement
   - Documentation

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript | Web UI |
| | D3.js v7+ | Topology visualization |
| | Zustand | State management |
| | Tailwind CSS | Styling |
| | Vite | Build tool |
| **API** | Python 3.10+ | Backend framework |
| | Flask | Web framework |
| | Flask-SQLAlchemy | ORM |
| | Marshmallow | Schema validation |
| | psycopg2 | PostgreSQL driver |
| | Gunicorn + Nginx | Deployment |
| **Database** | PostgreSQL 14+ | Persistent storage |
| **Telemetry** | Loki 2.x | Log aggregation |
| | Grafana 13.0.1 | Visualization |
| **Integration** | Kotlin (Aether) | MOFE runtime |
| | UWB Hardware / Emulation | Ranging capability |

---

## Key Design Decisions

1. **Thin Client**: Web client is lightweight; heavy lifting (MOFE, ranging, fusion) stays on runtime
2. **Stateless API**: API is stateless; state lives in MOFE runtime + PostgreSQL
3. **Gateway Pattern**: Root anchor is sole connection point; reduces API surface
4. **Telemetry by Default**: Every operation emits metrics for debugging
5. **Responsive First**: UI adapts to device; topology is primary focus
6. **Predicate Flexibility**: Geometric shapes are user-defined, not hardcoded

---

## Security Considerations

1. **Authentication**: Admin-only API access (default: ROOT anchor)
2. **Authorization**: Scope-based (API admin vs. node operations)
3. **Encryption**: HTTPS in production; TLS for internal communication
4. **Input Validation**: All inputs validated via Marshmallow schemas
5. **Rate Limiting**: Per-endpoint limits to prevent abuse
6. **Audit Trail**: All operations logged to mesh_events table

---

## Future Enhancements

1. **Mobile Native Clients** (iOS/Android) - Direct UWB integration
2. **Multi-Mesh Orchestration** - Manage multiple meshes from single console
3. **Advanced Predicates** - Custom Lua scripts, ML-based detection
4. **Replay/Playback** - Record and replay ranging sessions
5. **Advanced Analytics** - Drift detection, anchor health trending
6. **Distributed Admin** - Multi-admin support with role-based access

