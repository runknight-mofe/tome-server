from uuid import UUID

from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.mesh import NodeMesh, NodeMeshMembership, NodeMeshPredicateMembership
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
    # Workflow 1: Join a device to a mesh (requires an active user session)
    # -----------------------------------------------------------------------
    def join_mesh(self, device_id: UUID, mesh_id: UUID,
                  user_id: UUID, session_id: UUID,
                  roles: list[NodeMeshMembership.Role] | None = None,
                  is_anchor: bool = False, is_admin: bool = False,
                  is_root: bool = False) -> NodeMeshMembership | None:
        """
        Join a registered device to a mesh on behalf of an authenticated user.

        The device must already exist (registered via DeviceRepo.get_or_create).
        The session must be active and bound to this device — the caller is
        responsible for validating the session before calling this method
        (see UserSessionRepo.is_session_valid).

        Admin rights belong to the user, not the device.  is_admin expresses
        whether the user has administrative privileges in this mesh.

        Args:
            device_id:  UUID of the registered device joining
            mesh_id:    UUID of the mesh to join
            user_id:    UUID of the user acting through this device
            session_id: UUID of the active session authorising the membership
            roles:      List of NodeMeshMembership.Role enum values (default: empty)
            is_anchor:  True if device has fixed position in this mesh
            is_admin:   True if the user has admin rights in this mesh
            is_root:    True if device is the topology entry point

        Returns:
            NodeMeshMembership if successfully joined, None on failure
        """
        membership = NodeMeshMembership({
            NodeMeshMembership.DEVICE_ID  : device_id,
            NodeMeshMembership.MESH_ID    : mesh_id,
            NodeMeshMembership.USER_ID    : user_id,
            NodeMeshMembership.SESSION_ID : session_id,
            NodeMeshMembership.MESH_ROLES : roles or [],
            NodeMeshMembership.IS_ANCHOR  : is_anchor,
            NodeMeshMembership.IS_ADMIN   : is_admin,
            NodeMeshMembership.IS_ROOT    : is_root,
            NodeMeshMembership.JOINED_AT  : None,
            NodeMeshMembership.LAST_SEEN  : None,
        })
        return self.add(membership)
 
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
 
    def get_members_by_user(self, user_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all mesh memberships currently held by a user (across all devices/meshes).

        Args:
            user_id: UUID of the user

        Returns:
            Set of NodeMeshMembership objects for that user
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_members_by_user; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.user_id == user_id}

    def get_members_by_session(self, session_id: UUID) -> set[NodeMeshMembership]:
        """
        Get all mesh memberships backed by a specific session.

        Useful when a session expires: retrieve all memberships to drop.

        Args:
            session_id: UUID of the session

        Returns:
            Set of NodeMeshMembership objects for that session
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_members_by_session; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.session_id == session_id}

    def drop_memberships_for_session(self, session_id: UUID) -> list[NodeMeshMembership]:
        """
        Remove all mesh memberships backed by the given session.

        Called when a session expires (logout, inactivity, hard expiry) so
        that devices whose users are no longer present drop out of their meshes.

        Args:
            session_id: UUID of the expired/logged-out session

        Returns:
            List of removed NodeMeshMembership objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.drop_memberships_for_session; repo not initialized')

        to_remove = self.get_members_by_session(session_id)
        if not to_remove:
            return []
        return self.remove_many(to_remove)

    def get_user_in_mesh(self, user_id: UUID,
                         mesh_id: UUID) -> NodeMeshMembership | None:
        """
        Return the membership record for a specific user in a specific mesh.

        A user may only appear once per mesh (enforced by the one-active-session
        constraint), so at most one record is returned.

        Args:
            user_id: UUID of the user
            mesh_id: UUID of the mesh

        Returns:
            NodeMeshMembership if found, None otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_user_in_mesh; repo not initialized')

        with self._lock:
            for m in self.all_items:
                if m.user_id == user_id and m.mesh_id == mesh_id:
                    return m
        return None

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


# ---------------------------------------------------------------------------
# NodeMeshPredicateMembershipRepo
# Keys: [PREDICATE_ID, MESH_ID]  (composite identity)
# Predicates are independent resources shared across meshes via node_mesh_predicates.
# ---------------------------------------------------------------------------
class NodeMeshPredicateMembershipRepo(BaseRepository[NodeMeshPredicateMembership]):
    """Repository for NodeMeshPredicateMembership instances."""

    __model__ = NodeMeshPredicateMembership

    KEYS = [NodeMeshPredicateMembership.PREDICATE_ID, NodeMeshPredicateMembership.MESH_ID]

    def __init__(self, db: DBConnector | None = None,
                 db_params: dict | None = None):
        super().__init__(NodeMeshPredicateMembershipRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_node_mesh_predicate_memberships"
        self.sql[self.ADD]    = "add_many_node_mesh_predicate_memberships"
        self.sql[self.UPDATE] = "update_many_node_mesh_predicate_memberships"
        self.sql[self.REMOVE] = "remove_many_node_mesh_predicate_memberships"

    # -----------------------------------------------------------------------
    # Workflow 1: Join a predicate to a mesh
    # -----------------------------------------------------------------------
    def join_mesh(self, predicate_id: UUID, mesh_id: UUID,
                  position: int = 0) -> NodeMeshPredicateMembership | None:
        """
        Associate a registered predicate with a mesh at the given position.

        The predicate must already exist (created via PredicateRepo.add).
        A predicate may belong to multiple meshes simultaneously.

        Args:
            predicate_id: UUID of the registered predicate
            mesh_id: UUID of the mesh to join
            position: Ordered position within the mesh predicate list (default 0)

        Returns:
            NodeMeshPredicateMembership if successful, None on failure
        """
        membership = NodeMeshPredicateMembership({
            NodeMeshPredicateMembership.PREDICATE_ID : predicate_id,
            NodeMeshPredicateMembership.MESH_ID      : mesh_id,
            NodeMeshPredicateMembership.POSITION     : position,
        })
        return self.add(membership)

    # -----------------------------------------------------------------------
    # Workflow 2: Remove a predicate from a mesh
    # -----------------------------------------------------------------------
    def leave_mesh(self, predicate_id: UUID, mesh_id: UUID) -> bool:
        """
        Remove a predicate from a mesh.

        The predicate itself is not deleted; only the association is removed.
        The predicate may remain a member of other meshes.

        Args:
            predicate_id: UUID of the predicate leaving
            mesh_id: UUID of the mesh being left

        Returns:
            True if removal succeeded, False if membership not found
        """
        membership = self.get(predicate_id)
        if membership and membership.mesh_id == mesh_id:
            removed = self.remove(membership)
            return bool(removed)
        return False

    # -----------------------------------------------------------------------
    # Workflow 3: Update position within a mesh
    # -----------------------------------------------------------------------
    def update_membership(self, predicate_id: UUID, mesh_id: UUID,
                          position: int | None = None) -> NodeMeshPredicateMembership | None:
        """
        Update the ordered position of a predicate within a mesh.

        Args:
            predicate_id: UUID of the predicate
            mesh_id: UUID of the mesh
            position: New position (or None to keep existing)

        Returns:
            Updated NodeMeshPredicateMembership if found, None otherwise
        """
        membership = self.get(predicate_id)
        if not membership or membership.mesh_id != mesh_id:
            return None

        if position is not None:
            membership.position = position

        result = self.update(membership)
        return result if result else None

    # -----------------------------------------------------------------------
    # Filtering helpers — efficient in-memory lookups
    # -----------------------------------------------------------------------
    def get_predicates_by_mesh(self, mesh_id: UUID) -> set[NodeMeshPredicateMembership]:
        """
        Get all predicate memberships for a given mesh.

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Set of NodeMeshPredicateMembership objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_predicates_by_mesh; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.mesh_id == mesh_id}

    def get_meshes_for_predicate(self, predicate_id: UUID) -> set[NodeMeshPredicateMembership]:
        """
        Get all meshes that a predicate is a member of.

        Args:
            predicate_id: UUID of the predicate

        Returns:
            Set of NodeMeshPredicateMembership objects for that predicate
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_meshes_for_predicate; repo not initialized')

        with self._lock:
            return {m for m in self.all_items if m.predicate_id == predicate_id}

    def membership_count_for_mesh(self, mesh_id: UUID) -> int:
        """
        Fast count of predicates in a mesh.

        Args:
            mesh_id: UUID of the mesh

        Returns:
            Count of predicates in the mesh
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.membership_count_for_mesh; repo not initialized')

        with self._lock:
            return sum(1 for m in self.all_items if m.mesh_id == mesh_id)

    def membership_count_for_predicate(self, predicate_id: UUID) -> int:
        """
        Fast count of meshes a predicate participates in.

        Args:
            predicate_id: UUID of the predicate

        Returns:
            Count of meshes for that predicate
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.membership_count_for_predicate; repo not initialized')

        with self._lock:
            return sum(1 for m in self.all_items if m.predicate_id == predicate_id)
