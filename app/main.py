from  datetime import datetime
import logging
from traceback import print_exception
from uuid import uuid4

from com.runknight.math.geometry import Vector3
from packaging.version import Version

from com.aether.tome.db.predicate import PredicateRepo
from com.aether.tome.db.device import DeviceTypeRepo, DeviceRepo
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.mesh import MeshRepo
from com.aether.tome.model.mesh import NodeMesh, NodeMeshMembership
from com.aether.tome.model.device import Device, DeviceType
from com.aether.tome.model.predicate.base import Predicate
from com.aether.tome.model.predicate.geometric import Box, LineSegment, Plane, Point, Sphere

logging.basicConfig(level=logging.DEBUG, force=True)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.propagate = False

DB_PARAMS = {
    DBConnector.HOST : "10.0.0.6", 
    DBConnector.PORT : 15432,
    DBConnector.USER : "postgres",
    DBConnector.DB : "tome",
    DBConnector.PASS : "P@55w0rd!"
}


tome_db = DBConnector(DB_PARAMS)
nodes_db= DBConnector(DB_PARAMS)
device_types_db = DBConnector(DB_PARAMS)
pred_db = DBConnector(DB_PARAMS)

mr = MeshRepo(tome_db)
dr = DeviceRepo(nodes_db)
dtr = DeviceTypeRepo(device_types_db)
pr = PredicateRepo(pred_db)

try:
    if (not
        dr.initialize() or not
        mr.initialize() or not
        dtr.initialize() or not
        pr.initialize()
    ):
        raise RuntimeError("Failed to initialize at least one repo")
except RuntimeError as e:
    print_exception(e)
    quit()

def clear_all():
    mr.delete_all()
    dr.delete_all()
    pr.delete_all()

def create_test_nodes():

    EMULATED_GENERIC_TYPE = DeviceType.KnownTypes.EMULATED_GENERIC.value

    test_anchors = [
        Device({
            Device.ID           : uuid4(),
            Device.NAME         : "test_anchor1",
            Device.DESCRIPTION  : "Test Anchor 1",
            Device.TYPE         : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED  : True,
            Device.CREATED_AT   : datetime.now()
        }),

        Device({
            Device.ID : uuid4(),
            Device.NAME : "test_anchor2",
            Device.DESCRIPTION : "Test Anchor 2",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        }),

        Device({
            Device.ID : uuid4(),
            Device.NAME : "test_anchor3",
            Device.DESCRIPTION : "Test Anchor 3",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        }),

        Device({
            Device.ID : uuid4(),
            Device.NAME : "test_anchor4",
            Device.DESCRIPTION : "Test Anchor 4",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        })
    ]

    test_clients = [
        Device({
            Device.ID : uuid4(),
            Device.NAME : "test_client1",
            Device.DESCRIPTION : "Test Client 1",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        }),

        Device({
            Device.ID : uuid4(),
            Device.NAME : "test_client2",
            Device.DESCRIPTION : "Test Client 2",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        })
    ]

    test_remove_device = Device({
            Device.ID : uuid4(),
            Device.NAME : "test_removal_device",
            Device.DESCRIPTION : "Test Removal Device",
            Device.TYPE : EMULATED_GENERIC_TYPE,
            Device.IS_EMULATED : True,
            Device.CREATED_AT   : datetime.now()
        })

    # -------------------------------------------
    # Test ADD
    # -------------------------------------------
    added = dr.add(test_remove_device)
    assert added, "Failed to add node"

    addedNodes = [added]
    addedNodes.extend(dr.add_many(set(test_anchors)))
    addedNodes.extend(dr.add_many(set(test_clients)))
    
    assert addedNodes, "Failed to add nodes"
    assert len(addedNodes) == 7, f"Expected 7 added nodes; got {len(addedNodes)}"
    
    # -------------------------------------------
    # Test GET
    # -------------------------------------------
    retrieved_node = dr.get(field=Device.NAME, arg=test_anchors[0].name)
    assert retrieved_node, f"Failed to retrieve node {test_anchors[0].name}"

    # -------------------------------------------
    # Test UPDATE
    # -------------------------------------------
    tripped = False
    try:
        updated_desc = "Updated Root anchor description"
        retrieved_node.description = updated_desc
        updated = dr.update(retrieved_node)
    except Exception as e:
        tripped = isinstance(e, NotImplementedError)

    assert tripped, "Expected NotImplementedError to block updates to devices in DB"

    # -------------------------------------------
    # Test REMOVE
    # -------------------------------------------
    removed = dr.remove_by_id(added.id)
    assert removed, "Failed to remove node"
    assert removed.name == added.name, "Returned removed node name is mismatched"
    
    removed = dr.get(removed.id)
    assert not removed, "Failed to remove node"

    return dr.get_all()


def create_test_predicates():
    test_points = [
        Point({
            Point.LOCATION : Vector3.create(x=0.0, y=0.0, z=0.0),
            Point.ID : uuid4(),
            Point.NAME : "test_point1",
            Point.DESCRIPTION : "Test point 1",
            Point.IS_ACTIVE : True,
            Point.CREATED_AT : datetime.now(),
            Point.MODIFIED_AT : datetime.now(),
        }),
        Point({
            Point.LOCATION : Vector3.create(x=1.0, y=0.0, z=0.0),
            Point.ID : uuid4(),
            Point.NAME : "test_point2",
            Point.DESCRIPTION : "Test point 2",
            Point.IS_ACTIVE : True,
            Point.CREATED_AT : datetime.now(),
            Point.MODIFIED_AT : datetime.now(),
        }),
        Point({
            Point.LOCATION : Vector3.create(x=0.0, y=1.0, z=0.0),
            Point.ID : uuid4(),
            Point.NAME : "test_point3",
            Point.DESCRIPTION : "Test point 3",
            Point.IS_ACTIVE : True,
            Point.CREATED_AT : datetime.now(),
            Point.MODIFIED_AT : datetime.now(),
        }),
        Point({
            Point.LOCATION : Vector3.create(x=0.0, y=0.0, z=1.0),
            Point.ID : uuid4(),
            Point.NAME : "test_point4",
            Point.DESCRIPTION : "Test point 4",
            Point.IS_ACTIVE : True,
            Point.CREATED_AT : datetime.now(),
            Point.MODIFIED_AT : datetime.now(),
        }),
    ]

    test_line_segments = [
        LineSegment({
            LineSegment.START : Vector3.create(0.0, 0.0, 0.0),
            LineSegment.END : Vector3.create(1.0, 1.0, 1.0),
            LineSegment.ID : uuid4(),
            LineSegment.NAME : "test_line_segment1",
            LineSegment.DESCRIPTION : "Test Line Segment 1",
            LineSegment.IS_ACTIVE : True,
            LineSegment.CREATED_AT : datetime.now(),
            LineSegment.MODIFIED_AT : datetime.now(),
        }),
        LineSegment({
            LineSegment.START : Vector3.create(0.0, 0.0, 0.0),
            LineSegment.END : Vector3.create(1.0, 0.0, 0.0),
            LineSegment.ID : uuid4(),
            LineSegment.NAME : "test_line_segment2",
            LineSegment.DESCRIPTION : "Test Line Segment 2",
            LineSegment.IS_ACTIVE : True,
            LineSegment.CREATED_AT : datetime.now(),
            LineSegment.MODIFIED_AT : datetime.now(),
        }),
        LineSegment({
            LineSegment.START : Vector3.create(0.0, 0.0, 0.0),
            LineSegment.END : Vector3.create(0.0, 1.0, 0.0),
            LineSegment.ID : uuid4(),
            LineSegment.NAME : "test_line_segment3",
            LineSegment.DESCRIPTION : "Test Line Segment 3",
            LineSegment.IS_ACTIVE : True,
            LineSegment.CREATED_AT : datetime.now(),
            LineSegment.MODIFIED_AT : datetime.now(),
    }),
        LineSegment({
            LineSegment.START : Vector3.create(0.0, 0.0, 0.0),
            LineSegment.END : Vector3.create(0.0, 0.0, 1.0),
            LineSegment.ID : uuid4(),
            LineSegment.NAME : "test_line_segment4",
            LineSegment.DESCRIPTION : "Test Line Segment 4",
            LineSegment.IS_ACTIVE : True,
            LineSegment.CREATED_AT : datetime.now(),
            LineSegment.MODIFIED_AT : datetime.now(),
        }),
    ]

    test_planes = [
        Plane({
            Plane.POINT : Vector3.create(0.0, 0.0, 0.0),
            Plane.NORMAL : Vector3.create(1.0, 0.0, 0.0),
            Plane.ID : uuid4(),
            Plane.NAME : "test_plane1",
            Plane.DESCRIPTION : "Test Plane 1",
            Plane.IS_ACTIVE : True,
            Plane.CREATED_AT : datetime.now(),
            Plane.MODIFIED_AT : datetime.now(),
        }),
        Plane({
            Plane.POINT : Vector3.create(0.0, 0.0, 0.0),
            Plane.NORMAL : Vector3.create(0.0, 1.0, 0.0),
            Plane.ID : uuid4(),
            Plane.NAME : "test_plane2",
            Plane.DESCRIPTION : "Test Plane 2",
            Plane.IS_ACTIVE : True,
            Plane.CREATED_AT : datetime.now(),
            Plane.MODIFIED_AT : datetime.now(),
        }),
        Plane({
            Plane.POINT : Vector3.create(0.0, 0.0, 0.0),
            Plane.NORMAL : Vector3.create(0.0, 0.0, 1.0),
            Plane.ID : uuid4(),
            Plane.NAME : "test_plane3",
            Plane.DESCRIPTION : "Test Plane 3",
            Plane.IS_ACTIVE : True,
            Plane.CREATED_AT : datetime.now(),
            Plane.MODIFIED_AT : datetime.now(),
        }),
        Plane({
            Plane.POINT : Vector3.create(0.0, 0.0, 0.0),
            Plane.NORMAL : Vector3.create(1.0, 1.0, 1.0),
            Plane.ID : uuid4(),
            Plane.NAME : "test_plane4",
            Plane.DESCRIPTION : "Test Plane 4",
            Plane.IS_ACTIVE : True,
            Plane.CREATED_AT : datetime.now(),
            Plane.MODIFIED_AT : datetime.now(),
        }),
    ]

    test_spheres = [
        Sphere({
            Sphere.POINT : Vector3.create(0.0, 0.0, 0.0),
            Sphere.RADIUS : 1.0,
            Sphere.ID : uuid4(),
            Sphere.NAME : "test_sphere1",
            Sphere.DESCRIPTION : "Test Sphere 1",
            Sphere.IS_ACTIVE : True,
            Sphere.CREATED_AT : datetime.now(),
            Sphere.MODIFIED_AT : datetime.now(),
        }),
        Sphere({
            Sphere.POINT : Vector3.create(1.0, 0.0, 0.0),
            Sphere.RADIUS : 2.0,
            Sphere.ID : uuid4(),
            Sphere.NAME : "test_sphere2",
            Sphere.DESCRIPTION : "Test Sphere 2",
            Sphere.IS_ACTIVE : True,
            Sphere.CREATED_AT : datetime.now(),
            Sphere.MODIFIED_AT : datetime.now(),
        }),
        Sphere({
            Sphere.POINT : Vector3.create(0.0, 1.0, 0.0),
            Sphere.RADIUS : 3.0,
            Sphere.ID : uuid4(),
            Sphere.NAME : "test_sphere3",
            Sphere.DESCRIPTION : "Test Sphere 3",
            Sphere.IS_ACTIVE : True,
            Sphere.CREATED_AT : datetime.now(),
            Sphere.MODIFIED_AT : datetime.now(),
        }),
        Sphere({
            Sphere.POINT : Vector3.create(0.0, 0.0, 1.0),
            Sphere.RADIUS : 4.0,
            Sphere.ID : uuid4(),
            Sphere.NAME : "test_sphere4",
            Sphere.DESCRIPTION : "Test Sphere 4",
            Sphere.IS_ACTIVE : True,
            Sphere.CREATED_AT : datetime.now(),
            Sphere.MODIFIED_AT : datetime.now(),
        }),
    ]

    test_boxes = [

        Box({
            Box.MIN_EXTENT : Vector3.create(0.0, 0.0, 0.0),
            Box.MAX_EXTENT : Vector3.create(1.0, 1.0, 1.0),
            Box.ID : uuid4(),
            Box.NAME : "test_box1",
            Box.DESCRIPTION : "Test Box 1",
            Box.IS_ACTIVE : True,
            Box.CREATED_AT : datetime.now(),
            Box.MODIFIED_AT : datetime.now(),
        }),
        Box({
            Box.MIN_EXTENT : Vector3.create(-1.0, -1.0, -1.0),
            Box.MAX_EXTENT : Vector3.create(0.0, 0.0, 0.0),
            Box.ID : uuid4(),
            Box.NAME : "test_box2",
            Box.DESCRIPTION : "Test Box 2",
            Box.IS_ACTIVE : True,
            Box.CREATED_AT : datetime.now(),
            Box.MODIFIED_AT : datetime.now(),
        }),
        Box({
            Box.MIN_EXTENT : Vector3.create(-1.0, -1.0, -1.0),
            Box.MAX_EXTENT : Vector3.create(1.0, 1.0, 1.0),
            Box.ID : uuid4(),
            Box.NAME : "test_box3",
            Box.DESCRIPTION : "Test Box 3",
            Box.IS_ACTIVE : True,
            Box.CREATED_AT : datetime.now(),
            Box.MODIFIED_AT : datetime.now(),
        }),
        Box({
            Box.MIN_EXTENT : Vector3.create(1.0, 1.0, 1.0),
            Box.MAX_EXTENT : Vector3.create(-1.0, -1.0, -1.0),
            Box.ID : uuid4(),
            Box.NAME : "test_box4",
            Box.DESCRIPTION : "Test Box 4",
            Box.IS_ACTIVE : True,
            Box.CREATED_AT : datetime.now(),
            Box.MODIFIED_AT : datetime.now(),
        }),
    ]

    remove_point = Point({
        Point.LOCATION : Vector3.create(x=0.0, y=0.0, z=0.0),
        Point.ID : uuid4(),
        Point.NAME : "test_remove_point",
        Point.DESCRIPTION : "Test Remove Point",
        Point.IS_ACTIVE : True,
        Point.CREATED_AT : datetime.now(),
        Point.MODIFIED_AT : datetime.now(),
    })

    # -------------------------------------------
    # Test ADD
    # -------------------------------------------
    added = pr.add(remove_point)
    assert added, "Failed to add single predicate"
    added_points = [added]
    added_points.extend(pr.add_many(set(test_points)))
    assert added_points and len(added_points) == 5, f"Expected 4 added points; found {len(added_points)}"
    added_line_segments = pr.add_many(set(test_line_segments))
    assert added_line_segments and len(added_line_segments) == 4, f"Expected 4 added points; found {len(added_line_segments)}"
    added_planes = pr.add_many(set(test_planes))
    assert added_planes and len(added_planes) == 4, f"Expected 4 added points; found {len(added_planes)}"    
    added_spheres = pr.add_many(set(test_spheres))
    assert added_spheres and len(added_spheres) == 4, f"Expected 4 added points; found {len(added_spheres)}"
    added_boxes = pr.add_many(set(test_boxes))
    assert added_boxes and len(added_boxes) == 4, f"Expected 4 added points; found {len(added_boxes)}"


    # -------------------------------------------
    # Test GET
    # -------------------------------------------
    point = pr.get(added_points[0].id)
    assert point, f"Point {test_points[0].name} not found"
    line = pr.get(added_line_segments[0].id)
    assert line, f"Point {test_line_segments[0].name} not found"
    plane = pr.get(added_planes[0].id)
    assert plane, f"Point {test_planes[0].name} not found"
    sphere = pr.get(added_spheres[0].id)
    assert sphere, f"Point {test_spheres[0].name} not found"
    box = pr.get(added_boxes[0].id)
    assert box, f"Point {test_boxes[0].name} not found"

    # -------------------------------------------
    # Test UPDATE
    # -------------------------------------------
    updated_desc = "Updated point description"
    point.description = updated_desc
    updated = pr.update(point)
    assert updated and updated.description == updated_desc, "Failed to update predicate"

    # -------------------------------------------
    # Test REMOVE
    # -------------------------------------------
    removed = pr.remove_by_id(added.id)
    assert removed, "Failed to remove predicate"
    assert removed.name == added.name, "Returned removed predicate name mistached"
    removed = pr.get(removed.id)
    assert not removed, "Failed to remove predicate"

    preds = pr.get_all()
    return preds


def create_test_mesh(nodes: list[Device], predicates: list[Predicate]):

    mesh_id = uuid4()

    test_mesh_memberships = [
        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[0].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.ROOT ],
            NodeMeshMembership.IS_ADMIN     : True,
            NodeMeshMembership.IS_ANCHOR    : True,
            NodeMeshMembership.IS_ROOT      : True,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        }),

        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[1].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.MEMBER ],
            NodeMeshMembership.IS_ADMIN     : False,
            NodeMeshMembership.IS_ANCHOR    : True,
            NodeMeshMembership.IS_ROOT      : False,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        }),

        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[2].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.MEMBER ],
            NodeMeshMembership.IS_ADMIN     : False,
            NodeMeshMembership.IS_ANCHOR    : True,
            NodeMeshMembership.IS_ROOT      : False,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        }),

        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[3].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.MEMBER ],
            NodeMeshMembership.IS_ADMIN     : False,
            NodeMeshMembership.IS_ANCHOR    : True,
            NodeMeshMembership.IS_ROOT      : False,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        }),

        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[4].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.MEMBER ],
            NodeMeshMembership.IS_ADMIN     : False,
            NodeMeshMembership.IS_ANCHOR    : False,
            NodeMeshMembership.IS_ROOT      : False,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        }),

        NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID    : nodes[5].id,
            NodeMeshMembership.MESH_ID      : mesh_id,
            NodeMeshMembership.MESH_ROLES   : [ NodeMeshMembership.Role.MEMBER ],
            NodeMeshMembership.IS_ADMIN     : False,
            NodeMeshMembership.IS_ANCHOR    : False,
            NodeMeshMembership.IS_ROOT      : False,
            NodeMeshMembership.JOINED_AT    : datetime.now(),
            NodeMeshMembership.LAST_SEEN    : datetime.now(),
        })
    ]

    test_mesh = NodeMesh({
        NodeMesh.ID : mesh_id,
        NodeMesh.NAME : "test_mesh",
        NodeMesh.DESCRIPTION : "test mesh description",
        NodeMesh.NODES : test_mesh_memberships,
        NodeMesh.PREDICATES : predicates,
        NodeMesh.STATUS : NodeMesh.Status.QUORUM,
        NodeMesh.API_VERSION : Version("1.0.0")
    })

    remove_mesh = NodeMesh({
        NodeMesh.ID : uuid4(),
        NodeMesh.NAME : "test_remove_mesh",
        NodeMesh.DESCRIPTION : "test remove mesh description",
        NodeMesh.NODES : [],
        NodeMesh.PREDICATES : [],
        NodeMesh.STATUS : NodeMesh.Status.UNKNOWN,
        NodeMesh.API_VERSION : Version("1.0.0")
    })

    # -------------------------------------------
    # Test ADD
    # -------------------------------------------
    added = mr.add(test_mesh)
    assert added, f"Mesh {test_mesh.name} not added"
    added = mr.add(remove_mesh)
    assert added, f"Mesh {remove_mesh.name} not added"

    # -------------------------------------------
    # Test GET
    # -------------------------------------------
    retrieved = mr.get(added.id)
    assert retrieved, f"Mesh {test_mesh.name} could not be retrieved from repo"

    # -------------------------------------------
    # Test UPDATE
    # -------------------------------------------
    updated_version = Version("2.0.0")
    retrieved.api_version = updated_version
    updated = mr.update(retrieved)
    assert updated and updated.api_version == updated_version, "Failed to update mesh"
    
    # -------------------------------------------
    # Test REMOVE
    # -------------------------------------------
    removed = mr.remove_by_id(added.id)
    assert removed, "Failed to remove mesh"
    assert removed.name == added.name, "Returned removed mesh name mismatch"
    removed = mr.get(removed.id)
    assert not removed, "Failed to remove mesh"

    return mr.get_all()

if __name__ == "__main__":

    try:
#        print("noop")


        clear_all()

        nodes = create_test_nodes()
        assert nodes,                   "No nodes created"
        assert len(nodes) == 6,         "Nodes not right size"

        predicates = create_test_predicates()
        assert predicates,              "No predicates created"
        assert len(predicates) == 20,   "Predicates not right size"

        mesh = create_test_mesh(list(nodes), list(predicates))
        assert mesh,                    "No mesh created"

        clear_all()

        print("------SUCCESS!------")
        quit()

    except RuntimeError as e:
        print_exception(e)
