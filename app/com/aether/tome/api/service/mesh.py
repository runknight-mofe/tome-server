from app.com.aether.tome.db.predicate import PredicateRepo
from com.aether.tome.api.tome_config import config
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.mesh import MeshRepo, NodeMeshMembershipRepo

DB_PARAMS = {
    DBConnector.HOST : config.db_host, 
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB : config.db_name,
    DBConnector.PASS : config.db_pass
}

mmr = NodeMeshMembershipRepo(db_params=DB_PARAMS)
pr = PredicateRepo(db_params=DB_PARAMS)
mr = MeshRepo(db_params=DB_PARAMS)

assert mmr.initialize() and pr.initialize() and mr.initialize(), f"One or more repos failed to initialize"

def create_mesh(mesh):
    """Persists a mesh in the Tome db
    
    Adds a new mesh to the Tome DB
    
    Args:
        mesh (_NodeMesh_): node mesh to be persisted
    Returns:
        NodeMesh: Completed mesh object, if successful, None otherwise
    """
    return mr.add(mesh)

def delete_mesh(id):
    """Deletes an existing node mesh

    Args:
        id (_UUID_): Mesh unique identifier

    Returns:
        bool: True if successfully deleted, False otherwise
    """
    return mr.remove_by_id(id)

def retrieve_mesh(id):
    """Retrieve a node mesh from its ID

    Args:
        id (_UUID_): Node mesh unique identifier

    Returns:
        NodeMesh: Retrieved mesh if found, None otherwise
    """
    return mr.get(id)

def join_device_to_node_mesh(request):
    """Service request for device joining a node mesh"""
    pass

def remove_device_from_node_mesh(request):
    """Service request for device leaving node mesh"""
    pass

def set_roles_for_device_in_mesh(roles, device_id, mesh_id):
    """Update roles for for mesh member

    Sets the roles for a device within the given mesh, provided it is a member

    Args:
        roles (_list[NodeMeshMembership.Role_): roles to assign
        device_id (_UUID_):  mesh member device
        mesh_id (_UUID_):  node mesh
    
    """
    
    updated = mmr.update_membership(roles=roles, device_id=device_id, mesh_id=mesh_id)
    if updated:
        return updated.mesh_roles == roles
    return False
    
def set_root_device_for_mesh(device_id, mesh_id):
    """Change the root device for a mesh

    Drops existing root flag, then raises root flag for provided device

    Args:
        device_id (_UUID_): Mesh member to make root
        mesh_id (_UUID_): Mesh being affected
        
    Raises:
        RuntimeException: if an intermediate step in the process fails
        
    Returns:
        bool: True if the root shifts to the designated mesh member device, False otherwise
    """
    
    prev_root = mmr.get_root_for_mesh(mesh_id)
    assert prev_root, f"Failed to retrieve existing root device for mesh {mesh_id}"
    assert mmr.update_membership(is_root=False, device_id=prev_root.device_id, mesh_id=mesh_id), f"Failed to drop root for {prev_root} in mesh {mesh_id}"
    return mmr.update_membership(is_root=True, device_id=device_id, mesh_id=mesh_id) is not None

def set_admin_for_device_in_mesh(is_admin, device_id, mesh_id):
    """Set admin for a mesh member

    Raises or lowers admin flag for a mesh member

    Args:
        is_admin (_bool_): admin flag
        device_id (_UUID_): Mesh member device
        mesh_id (_UUID_): Mesh being affected

    Returns:
        bool| True if the admin flag was updated, False otherwise
    """
    return mmr.update_membership(is_admin=is_admin, device_id=device_id,mesh_id=mesh_id) is not None

def set_anchor_for_device_in_mesh(is_anchor, device_id, mesh_id):
    """Set anchor status for a mesh member

    Raises or lowers anchor flag for a mesh member.  
    A raised flag indicates the device is an ANCHOR node.  
    A lowered flag indicates the device is a CLIENT node.

    Args:
        is_anchor (_bool_): anchor flag
        device_id (_UUID_): Mesh member device
        mesh_id (_UUID_): Mesh being affected

    Returns:
        bool| True if the anchor flag was updated, False otherwise
    """
    return mmr.update_membership(is_anchor=is_anchor, device_id=device_id,mesh_id=mesh_id) is not None

def add_predicate_to_node_mesh(predicate, mesh_id):
    """Service request for adding a predicate to a node mesh"""
    return pr.add(predicate)

def remove_predicate_to_node_mesh(predicate, mesh_id):
    """Service request for removing a predicate from a node mesh"""
    pass