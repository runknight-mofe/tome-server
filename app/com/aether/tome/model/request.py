from dataclasses import dataclass
from typing import Type
from uuid import UUID

from com.runknight.model.base_model import BaseDataModel

from com.aether.tome.model.mesh import NodeMeshMembership, NodeMeshPredicateMembership

@dataclass(eq=False)
class NodeMeshMembershipRequest(BaseDataModel):
    """Represents the request from a resident device to join or modify a node mesh membership"""

    DEVICE_ID   = "device_id"
    MESH_ID     = "mesh_id"
    ROLES       = "roles"
    ANCHOR      = "anchor"
    ADMIN       = "admin"
    ROOT        = "root"
    
    REQUIRED_FIELDS = { DEVICE_ID : str, MESH_ID : str, ROLES: list,  }
    OPTIONAL_FIELDS = { ANCHOR : bool, ADMIN : bool, ROOT : bool }
    FIELD_TYPES = { ROLES : list[NodeMeshMembership.Role] }
    DEFAULT_VALUES = { ANCHOR : False, ADMIN : False, ROOT : False }

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMeshMembershipRequest.REQUIRED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMeshMembershipRequest.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return  BaseDataModel.get_field_types() | NodeMeshMembershipRequest.FIELD_TYPES
    
    @staticmethod
    def get_default_values():
        return NodeMeshMembershipRequest.DEFAULT_VALUES

    def __init__(self, params):
        super().__init__(params)
        self._device_id: UUID = self._data[NodeMeshMembershipRequest.DEVICE_ID]
        self._mesh_id: UUID = self._data[NodeMeshMembershipRequest.MESH_ID]
        self._roles: list[NodeMeshMembership.Role] = self._data[NodeMeshMembershipRequest.ROLES]
        self._anchor: bool = self._data[NodeMeshMembershipRequest.ANCHOR]
        self._admin: bool = self._data[NodeMeshMembershipRequest.ADMIN]
        self._root: bool = self._data[NodeMeshMembershipRequest.ROOT]


    @property
    def device_id(self):
        """Unique identifier of the physical device"""
        return self._device_id

    @device_id.setter
    def device_id(self, value : UUID):
        self._device_id = value
        self.set_field_value(NodeMeshMembershipRequest.DEVICE_ID, value)

    @property
    def mesh_id(self):
        """Unique identifier of the node mesh being"""
        return self._mesh_id

    @mesh_id.setter
    def mesh_id(self, value : UUID):
        self._mesh_id = value
        self.set_field_value(NodeMeshMembershipRequest.MESH_ID, value)

    @property
    def roles(self):
        """List of roles requested for the joining device"""
        return self._roles

    @roles.setter
    def roles(self, value : list[NodeMeshMembership.Role]):
        self._roles = value
        self.set_field_value(NodeMeshMembershipRequest.ROLES, value)

    @property
    def anchor(self):
        """Is device requesting to be an anchor?"""
        return self._anchor

    @anchor.setter
    def anchor(self, value : bool):
        self._anchor = value
        self.set_field_value(NodeMeshMembershipRequest.ANCHOR, value)
        
    @property
    def admin(self):
        """Is device requesting to be an admin?"""
        return self._admin

    @admin.setter
    def admin(self, value : bool):
        self._admin = value
        self.set_field_value(NodeMeshMembershipRequest.ADMIN, value)
        
    @property
    def root(self):
        """Is device requesting to be the root node?"""
        return self._root

    @root.setter
    def root(self, value : bool):
        self._root = value
        self.set_field_value(NodeMeshMembershipRequest.ROOT, value)


@dataclass(eq=False)
class NodeMeshPredicateMembershipRequest(BaseDataModel):
    """Represents the request to associate a predicate with a node mesh"""

    PREDICATE_ID = "predicate_id"
    MESH_ID      = "mesh_id"
    POSITION     = "position"

    REQUIRED_FIELDS = { PREDICATE_ID: str, MESH_ID: str }
    OPTIONAL_FIELDS = { POSITION: int }
    FIELD_TYPES     = { PREDICATE_ID: UUID, MESH_ID: UUID, POSITION: int }
    DEFAULT_VALUES  = { POSITION: 0 }

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMeshPredicateMembershipRequest.REQUIRED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMeshPredicateMembershipRequest.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return BaseDataModel.get_field_types() | NodeMeshPredicateMembershipRequest.FIELD_TYPES

    @staticmethod
    def get_default_values():
        return NodeMeshPredicateMembershipRequest.DEFAULT_VALUES

    def __init__(self, params):
        super().__init__(params)
        self._predicate_id : UUID = self._data[NodeMeshPredicateMembershipRequest.PREDICATE_ID]
        self._mesh_id      : UUID = self._data[NodeMeshPredicateMembershipRequest.MESH_ID]
        self._position     : int  = self._data[NodeMeshPredicateMembershipRequest.POSITION]

    @property
    def predicate_id(self):
        """Unique identifier of the predicate"""
        return self._predicate_id

    @predicate_id.setter
    def predicate_id(self, value: UUID):
        self._predicate_id = value
        self.set_field_value(NodeMeshPredicateMembershipRequest.PREDICATE_ID, value)

    @property
    def mesh_id(self):
        """Unique identifier of the node mesh"""
        return self._mesh_id

    @mesh_id.setter
    def mesh_id(self, value: UUID):
        self._mesh_id = value
        self.set_field_value(NodeMeshPredicateMembershipRequest.MESH_ID, value)

    @property
    def position(self):
        """Ordered position of the predicate within the mesh"""
        return self._position

    @position.setter
    def position(self, value: int):
        self._position = value
        self.set_field_value(NodeMeshPredicateMembershipRequest.POSITION, value)