from com.runknight.tome.db.base_repository import BaseRepository
from com.runknight.tome.db.connection import DBConnector
from com.runknight.tome.model.mesh import NodeMesh, NodeMeshMembership
from com.runknight.tome.model.node import Node

# ---------------------------------------------------------------------------
# MeshRepo  (the original repo from db/__init__.py)
# Keys: [ID, NAME]
# status is a NodeMeshStatus ordinal INT in the DB; Python enum reconstructs
# the full object from that ordinal without a JOIN.
# nodes resolves to List[Node] via node_mesh_devices join table.
# predicates resolves to List[Predicate] via node_mesh_predicates join table.
# ---------------------------------------------------------------------------
class MeshRepo(BaseRepository[NodeMesh]):
    """Data repository managing instances of NodeMesh """
    
    __model__ = NodeMesh

    KEYS = [NodeMesh.ID, NodeMesh.NAME]
    
    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(MeshRepo.KEYS, db, db_params)
        self.sql[self.GET]      = "get_all_node_meshes"
        self.sql[self.ADD]      = "add_many_node_meshes"
        self.sql[self.UPDATE]   = "update_many_node_meshes"
        self.sql[self.REMOVE]   = "remove_many_node_meshes"

# ---------------------------------------------------------------------------
# NodeRepo
# Manages physical hardware platform definitions.
# Keys: [ID, NAME]
# ---------------------------------------------------------------------------
class NodeRepo(BaseRepository[Node]):
    """Data repository managing instances of NodeMesh """
    
    __model__ = Node

    KEYS = [Node.ID, Node.NAME]
    
    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(NodeRepo.KEYS, db, db_params)
        self.sql[self.GET]      = "get_all_node_devices"
        self.sql[self.ADD]      = "add_many_node_devices"
        self.sql[self.UPDATE]   = "update_many_node_devices"
        self.sql[self.REMOVE]   = "remove_many_node_devices"


# ---------------------------------------------------------------------------
# NodeMeshMembershipRepo
# Keys: [NODE_ID, MESH_ID]  (composite identity)
# mesh_roles round-trips as INT[] of ordinals; the Python NodeMeshRole enum
# reconstructs full objects from those ordinals without a DB query.
# ---------------------------------------------------------------------------
class NodeMeshMembershipRepo(BaseRepository[NodeMeshMembership]):
    """Repository for NodeMeshMembership instances."""
 
    __model__ = NodeMeshMembership

    KEYS = [NodeMeshMembership.NODE_ID, NodeMeshMembership.MESH_ID]
 
    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(NodeMeshMembershipRepo.KEYS, db, db_params)
        self.sql[self.GET]      = "get_all_node_mesh_memberships"
        self.sql[self.ADD]      = "add_many_node_mesh_memberships"
        self.sql[self.UPDATE]   = "update_many_node_mesh_memberships"
        self.sql[self.REMOVE]   = "remove_many_node_mesh_memberships"
 