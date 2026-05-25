from com.aether.tome.api.tome_config import config
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.mesh import MeshRepo, NodeMeshMembershipRepo, NodeMeshPredicateMembershipRepo
from com.aether.tome.db.predicate import PredicateRepo
from com.aether.tome.model.mesh import NodeMeshMembership

DB_PARAMS = {
    DBConnector.HOST : config.db_host,
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB   : config.db_name,
    DBConnector.PASS : config.db_pass
}

mmr = NodeMeshMembershipRepo(db_params=DB_PARAMS)
pmr = NodeMeshPredicateMembershipRepo(db_params=DB_PARAMS)
pr  = PredicateRepo(db_params=DB_PARAMS)
mr  = MeshRepo(db_params=DB_PARAMS)

assert mmr.initialize() and pmr.initialize() and pr.initialize() and mr.initialize(), \
    "One or more repos failed to initialize"


def create_mesh(mesh):
    """Persist a new mesh to the Tome DB."""
    return mr.add(mesh)


def delete_mesh(id):
    """Delete an existing node mesh by ID."""
    return mr.remove_by_id(id)


def retrieve_mesh(id):
    """Retrieve a node mesh by its UUID."""
    return mr.get(id)


# ---------------------------------------------------------------------------
# Device membership
# ---------------------------------------------------------------------------

def join_device_to_node_mesh(request):
    """Join a registered device to a node mesh.

    Args:
        request: NodeMeshMembershipRequest with device_id, mesh_id, roles, and flags

    Returns:
        NodeMeshMembership if successful, None otherwise
    """
    return mmr.join_mesh(
        device_id=request.device_id,
        mesh_id=request.mesh_id,
        roles=request.roles,
        is_anchor=request.anchor,
        is_admin=request.admin,
        is_root=request.root,
    )


def remove_device_from_node_mesh(request):
    """Remove a device from a node mesh.

    Args:
        request: NodeMeshMembershipRequest with device_id and mesh_id

    Returns:
        True if removed successfully, False otherwise
    """
    return mmr.leave_mesh(device_id=request.device_id, mesh_id=request.mesh_id)


def set_roles_for_device_in_mesh(roles, device_id, mesh_id):
    """Update roles for a mesh member.

    Args:
        roles: list[NodeMeshMembership.Role] to assign
        device_id: UUID of the mesh member device
        mesh_id: UUID of the node mesh
    """
    updated = mmr.update_membership(roles=roles, device_id=device_id, mesh_id=mesh_id)
    if updated:
        return updated.mesh_roles == roles
    return False


def set_root_device_for_mesh(device_id, mesh_id):
    """Change the root device for a mesh.

    Drops the existing root flag then raises it for the provided device.

    Args:
        device_id: UUID of the mesh member to make root
        mesh_id: UUID of the mesh being affected

    Returns:
        bool: True if the root shifts to the designated device
    """
    prev_root = mmr.get_root_for_mesh(mesh_id)
    assert prev_root, f"Failed to retrieve existing root device for mesh {mesh_id}"
    assert mmr.update_membership(is_root=False, device_id=prev_root.device_id, mesh_id=mesh_id), \
        f"Failed to drop root for {prev_root} in mesh {mesh_id}"
    return mmr.update_membership(is_root=True, device_id=device_id, mesh_id=mesh_id) is not None


def set_admin_for_device_in_mesh(is_admin, device_id, mesh_id):
    """Raise or lower the admin flag for a mesh member.

    Args:
        is_admin: bool
        device_id: UUID of the mesh member device
        mesh_id: UUID of the mesh being affected
    """
    return mmr.update_membership(is_admin=is_admin, device_id=device_id, mesh_id=mesh_id) is not None


def set_anchor_for_device_in_mesh(is_anchor, device_id, mesh_id):
    """Raise or lower the anchor flag for a mesh member.

    A raised flag indicates an ANCHOR node; lowered indicates a CLIENT node.

    Args:
        is_anchor: bool
        device_id: UUID of the mesh member device
        mesh_id: UUID of the mesh being affected
    """
    return mmr.update_membership(is_anchor=is_anchor, device_id=device_id, mesh_id=mesh_id) is not None


# ---------------------------------------------------------------------------
# Predicate membership
# ---------------------------------------------------------------------------

def join_predicate_to_mesh(request):
    """Associate an existing predicate with a node mesh.

    The predicate must already exist (created via the predicate service).
    A predicate may belong to multiple meshes simultaneously.

    Args:
        request: NodeMeshPredicateMembershipRequest with predicate_id, mesh_id, position

    Returns:
        NodeMeshPredicateMembership if successful, None otherwise
    """
    return pmr.join_mesh(
        predicate_id=request.predicate_id,
        mesh_id=request.mesh_id,
        position=request.position,
    )


def remove_predicate_from_mesh(request):
    """Remove a predicate from a node mesh.

    The predicate itself is not deleted; only the association is removed.

    Args:
        request: NodeMeshPredicateMembershipRequest with predicate_id and mesh_id

    Returns:
        True if removed successfully, False otherwise
    """
    return pmr.leave_mesh(predicate_id=request.predicate_id, mesh_id=request.mesh_id)


def update_predicate_position_in_mesh(request):
    """Update the ordered position of a predicate within a mesh.

    Args:
        request: NodeMeshPredicateMembershipRequest with predicate_id, mesh_id, position

    Returns:
        NodeMeshPredicateMembership if updated, None otherwise
    """
    return pmr.update_membership(
        predicate_id=request.predicate_id,
        mesh_id=request.mesh_id,
        position=request.position,
    )


def get_predicates_in_mesh(mesh_id):
    """Retrieve all predicates associated with a mesh, ordered by position.

    Resolves NodeMeshPredicateMembership records into full Predicate objects.

    Args:
        mesh_id: UUID of the mesh

    Returns:
        list[Predicate] ordered by position ascending
    """
    memberships = pmr.get_predicates_by_mesh(mesh_id)
    ordered = sorted(memberships, key=lambda m: m.position)
    predicates = []
    for m in ordered:
        predicate = pr.get(m.predicate_id)
        if predicate:
            predicates.append(predicate)
    return predicates
