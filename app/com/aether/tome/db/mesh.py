from uuid import UUID

from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.mesh import NodeMesh, NodeMeshMembership
from com.aether.tome.model.node import Node

# ---------------------------------------------------------------------------
# MeshRepo (unchanged from before)
# Keys: [ID, NAME]
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
# NodeMeshMembershipRepo — ENHANCED with device_id semantics
# Keys: [DEVICE_ID, MESH_ID]  (composite identity, CHANGED from NODE_ID)
# mesh_roles round-trips as INT[] of ordinals; Python enum reconstructs.
# ---------------------------------------------------------------------------
class NodeMeshMembershipRepo(BaseRepository[NodeMeshMembership]):
    """Repository for NodeMeshMembership instances."""
 
    __model__ = NodeMeshMembership

    KEYS = [NodeMeshMembership.DEVICE_ID, NodeMeshMembership.MESH_ID]
 
    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(NodeMeshMembershipRepo.KEYS, db, db_params)
        self.sql[self.GET]      = "get_all_node_mesh_memberships"
        self.sql[self.ADD]      = "add_many_node_mesh_memberships"
        self.sql[self.UPDATE]   = "update_many_node_mesh_memberships"
        self.sql[self.REMOVE]   = "remove_many_node_mesh_memberships"
 
    # -----------------------------------------------------------------------
    # Workflow 1: Join a device to a mesh
    # -----------------------------------------------------------------------
    def join_mesh(self, device_id: UUID, mesh_id: UUID, 
                  roles: list[NodeMeshMembership.Role] | None = None,
                  is_anchor: bool = False, is_admin: bool = False,
                  is_root: bool = False) -> NodeMeshMembership | None:
        """
        Join a registered device to a mesh with specified topology roles.

        The device must already exist (registered via DeviceRepo.get_or_create).
        This method creates the membership relationship with context-specific flags.

        Args:
            device_id: UUID of the registered device joining
            mesh_id: UUID of the mesh to join
            roles: List of NodeMeshMembership.Role enum values (default: empty)
            is_anchor: True if device has fixed position in this mesh
            is_admin: True if device has admin rights in this mesh
            is_root: True if device is the topology entry point

        Returns:
            NodeMeshMembership if successfully joined, None on failure

        Example:
            # Device already registered
            device = device_repo.get_or_create("tag_001", device_type_ordinal=14)
            
            # Now join it to a mesh
            membership = membership_repo.join_mesh(
                device_id=device.id,
                mesh_id=mesh_id,
                roles=[NodeMeshMembership.Role.MEMBER],
                is_anchor=False
            )
        """
        membership = NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID: device_id,
            NodeMeshMembership.MESH_ID: mesh_id,
            NodeMeshMembership.MESH_ROLES: roles or [],
            NodeMeshMembership.IS_ANCHOR: is_anchor,
            NodeMeshMembership.IS_ADMIN: is_admin,
            NodeMeshMembership.IS_ROOT: is_root,
            NodeMeshMembership.JOINED_AT: None,  # DB sets timestamps
            NodeMeshMembership.LAST_SEEN: None, # DB sets timestamps
        })
        result = self.add(membership)
        return result
 
    # -----------------------------------------------------------------------
    # Workflow 2: Device leaves a mesh
    # -----------------------------------------------------------------------
    def leave_mesh(self, device_id: UUID, mesh_id: UUID) -> bool:
        """
        Remove a device from a mesh.

        Verifies that the device exists in the local repo with the matching
        mesh_id before deletion to avoid false positives.

        Args:
            device_id: UUID of the device leaving
            mesh_id: UUID of the mesh being left

        Returns:
            True if removal succeeded, False if membership not found

        Example:
            success = membership_repo.leave_mesh(device_id, mesh_id)
            if success:
                print(f"Device {device_id} left mesh {mesh_id}")
        """
        membership = self.get(device_id)
        if membership and membership.mesh_id == mesh_id:
            removed = self.remove(membership)
            return bool(removed)
        return False
 
    # -----------------------------------------------------------------------
    # Workflow 3: Update existing membership
    # -----------------------------------------------------------------------
    def update_membership(self, device_id: UUID, mesh_id: UUID,
                         roles: list[NodeMeshMembership.Role] | None = None,
                         is_anchor: bool | None = None,
                         is_admin: bool | None = None,
                         is_root: bool | None = None) -> NodeMeshMembership | None:
        """
        Update membership flags and roles.

        Only supplied fields are updated (None values are ignored).
        This avoids re-sending unchanged fields to the database.

        Args:
            device_id: UUID of the device in the membership
            mesh_id: UUID of the mesh
            roles: New list of roles (or None to keep existing)
            is_anchor: New anchor flag (or None to keep existing)
            is_admin: New admin flag (or None to keep existing)
            is_root: New root flag (or None to keep existing)

        Returns:
            Updated NodeMeshMembership if found, None if not found or update failed

        Example:
            # Promote device to anchor (only change is_anchor)
            updated = membership_repo.update_membership(
                device_id=device_id,
                mesh_id=mesh_id,
                is_anchor=True  # Only this field changes
            )
        """
        membership = self.get(device_id)  # CHANGED from node_id
        if not membership or membership.mesh_id != mesh_id:
            return None
 
        # Selectively update only supplied fields
        if roles is not None:
            membership.mesh_roles = roles
        if is_anchor is not None:
            membership.is_anchor = is_anchor
        if is_admin is not None:
            membership.is_admin = is_admin
        if is_root is not None:
            membership.is_root = is_root
 
        result = self.update(membership)
        return result if result else None
 
    # -----------------------------------------------------------------------
    # Filtering helpers — efficient in-memory lookups
    # -----------------------------------------------------------------------
    def get_members_by_mesh(self, mesh_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all device memberships for a given mesh.

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Set of NodeMeshMembership objects (device references)
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_members_by_mesh; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.mesh_id == mesh_id}
 
    def get_anchors_for_mesh(self, mesh_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all anchor devices in a mesh (fixed-position infrastructure).

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Set of anchor NodeMeshMembership objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_anchors_for_mesh; repo not initialized')

        with self._lock:
            return {m for m in self.all_items 
                    if m.mesh_id == mesh_id and m.is_anchor}
 
    def get_clients_for_mesh(self, mesh_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all client (mobile/tag) devices in a mesh.

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Set of client NodeMeshMembership objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_clients_for_mesh; repo not initialized')

        with self._lock:
            return {m for m in self.all_items 
                    if m.mesh_id == mesh_id and not m.is_anchor}
 
    def get_root_for_mesh(self, mesh_id: UUID) -> NodeMeshMembership | None:
        """
        Get the root device for a mesh (topology entry point, should be unique).

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Root NodeMeshMembership if one exists, None otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_root_for_mesh; repo not initialized')

        with self._lock:
            roots = {m for m in self.all_items 
                     if m.mesh_id == mesh_id and m.is_root}
            return roots.pop() if roots else None
 
    def get_members_with_role(self, mesh_id: UUID, 
                             role: NodeMeshMembership.Role) -> set[NodeMeshMembership]:
        """
        Get all devices with a specific role in a mesh.

        Args:
            mesh_id: UUID of the mesh
            role: NodeMeshMembership.Role enum value to filter by

        Returns:
            Set of NodeMeshMembership objects with the specified role
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_members_with_role; repo not initialized')

        with self._lock:
            return {m for m in self.all_items 
                    if m.mesh_id == mesh_id and role in m.mesh_roles}

    def get_admins_for_mesh(self, mesh_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all administrative devices in a mesh.

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Set of admin NodeMeshMembership objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_admins_for_mesh; repo not initialized')

        with self._lock:
            return {m for m in self.all_items 
                    if m.mesh_id == mesh_id and m.is_admin}

    def get_meshes_for_device(self, device_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all meshes that a device is a member of.

        Useful for finding all topologies a device participates in.

        Args:
            device_id: UUID of the device

        Returns:
            Set of NodeMeshMembership objects for that device
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_meshes_for_device; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.device_id == device_id}

    def membership_count_for_mesh(self, mesh_id: UUID) -> int:
        """
        Fast count of device members in a mesh (no object construction).

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Count of devices in the mesh
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.membership_count_for_mesh; repo not initialized')

        with self._lock:
            return sum(1 for m in self.all_items if m.mesh_id == mesh_id)
 
    def membership_count_for_device(self, device_id: UUID) -> int:
        """
        Fast count of meshes a device participates in (no object construction).
        
        Args:
            device_id: UUID of the device
        
        Returns:
            Count of meshes for that device
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.membership_count_for_device; repo not initialized')
        
        with self._lock:
            return sum(1 for m in self.all_items if m.device_id == device_id)
 