from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Type
from uuid import UUID

from com.runknight.model.base_model import BaseDataModel
from packaging.version import Version
from com.aether.tome.model.predicate.base import Predicate


@dataclass(eq=False)
class NodeMeshPredicateMembership(BaseDataModel):
    """Describes membership of a predicate within a mesh topology instance"""

    PREDICATE_ID = "predicate_id"
    MESH_ID      = "mesh_id"
    POSITION     = "position"

    EXPECTED_FIELDS = { PREDICATE_ID: str, MESH_ID: str, POSITION: int }
    OPTIONAL_FIELDS = {}
    FIELD_TYPES = {
        PREDICATE_ID : UUID,
        MESH_ID      : UUID,
        POSITION     : int,
    }

    def __init__(self, params):
        super().__init__(params)
        self._predicate_id : UUID = self._data[NodeMeshPredicateMembership.PREDICATE_ID]
        self._mesh_id      : UUID = self._data[NodeMeshPredicateMembership.MESH_ID]
        self._position     : int  = self._data[NodeMeshPredicateMembership.POSITION]

    @property
    def predicate_id(self):
        """Predicate unique identifier"""
        return self._predicate_id

    @predicate_id.setter
    def predicate_id(self, value: UUID):
        self._predicate_id = value
        self.set_field_value(NodeMeshPredicateMembership.PREDICATE_ID, value)

    @property
    def mesh_id(self):
        """Mesh unique identifier"""
        return self._mesh_id

    @mesh_id.setter
    def mesh_id(self, value: UUID):
        self._mesh_id = value
        self.set_field_value(NodeMeshPredicateMembership.MESH_ID, value)

    @property
    def position(self):
        """Ordered position of the predicate within the mesh"""
        return self._position

    @position.setter
    def position(self, value: int):
        self._position = value
        self.set_field_value(NodeMeshPredicateMembership.POSITION, value)

    def __hash__(self):
        return hash((self.predicate_id, self.mesh_id))

    def __str__(self):
        return f'[{self.mesh_id},{self.predicate_id}]: pos={self.position}'

    def __repr__(self) -> str:
        return f'[{self.mesh_id},{self.predicate_id}]: pos={self.position}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMeshPredicateMembership.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMeshPredicateMembership.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return NodeMeshPredicateMembership.FIELD_TYPES


@dataclass(eq = False)
class NodeMeshMembership(BaseDataModel):
    """Describes membership of a node within a mesh topology instance"""

    class Role(Enum):
        """Responsibility of the node within the mesh"""
        MEMBER  = 0
        GATEWAY = 1
        ADMIN   = 2
        ROOT    = 3

    DEVICE_ID   = "device_id"
    MESH_ID     = "mesh_id"
    MESH_ROLES  = "mesh_roles"
    IS_ADMIN    = "is_admin"
    IS_ANCHOR   = "is_anchor"
    IS_ROOT     = "is_root"
    JOINED_AT   = "joined_at"
    LAST_SEEN   = "last_seen"

    EXPECTED_FIELDS = { DEVICE_ID : str, MESH_ID : str, MESH_ROLES : list, IS_ADMIN : bool, IS_ANCHOR: bool, IS_ROOT : bool, JOINED_AT : str, LAST_SEEN : str }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        MESH_ID : UUID,
        DEVICE_ID : UUID,
        MESH_ROLES : list[Role],
        IS_ADMIN : bool,
        IS_ANCHOR : bool,
        IS_ROOT : bool,
        JOINED_AT : datetime,
        LAST_SEEN : datetime
    }

    def __init__(self, params):
        super().__init__(params)
        self._mesh_id : UUID                                = self._data[NodeMeshMembership.MESH_ID]
        self._device_id : UUID                              = self._data[NodeMeshMembership.DEVICE_ID]
        self._is_anchor : bool                              = self._data[NodeMeshMembership.IS_ANCHOR]
        self._mesh_roles : list[NodeMeshMembership.Role]    = self._data[NodeMeshMembership.MESH_ROLES] if NodeMeshMembership.MESH_ROLES in self._data else []
        self._is_admin : bool                               = self._data[NodeMeshMembership.IS_ADMIN]
        self._is_root : bool                                = self._data[NodeMeshMembership.IS_ROOT]
        self._joined_at : datetime                          = self._data[NodeMeshMembership.JOINED_AT]
        self._last_seen : datetime                          = self._data[NodeMeshMembership.LAST_SEEN]

    @property
    def mesh_id(self):
        """Mesh unique identifier"""
        return self._mesh_id

    @mesh_id.setter
    def mesh_id(self, value : UUID):
        self._mesh_id = value
        self.set_field_value(NodeMeshMembership.MESH_ID, value)

    @property
    def device_id(self):
        """Device unique identifier"""
        return self._device_id

    @device_id.setter
    def device_id(self, value : UUID):
        self._device_id = value
        self.set_field_value(NodeMeshMembership.DEVICE_ID, value)

    @property
    def is_anchor(self):
        """Is the device an anchor (fixed position) in this mesh?"""
        return self._is_anchor

    @is_anchor.setter
    def is_anchor(self, value : bool):
        self._node_type = value
        self.set_field_value(NodeMeshMembership.IS_ANCHOR, value)

    @property
    def mesh_roles(self):
        """Roles for associated device within mesh"""
        return self._mesh_roles

    @mesh_roles.setter
    def mesh_roles(self, value : list[Role]):
        self._mesh_roles = value
        self.set_field_value(NodeMeshMembership.MESH_ROLES, value)

    @property
    def is_admin(self):
        """Does the device have admin privileges in this mesh?"""
        return self._is_admin

    @is_admin.setter
    def is_admin(self, value : bool):
        self._is_admin = value
        self.set_field_value(NodeMeshMembership.IS_ADMIN, value)

    @property
    def is_root(self):
        """Is the node the root of the mesh"""
        return self._is_root

    @is_root.setter
    def is_root(self, value : bool):
        self._is_root = value
        self.set_field_value(NodeMeshMembership.IS_ROOT, value)


    @property
    def joined_at(self):
        """Timestamp when device joined this mesh."""
        return self._joined_at

    @joined_at.setter
    def joined_at(self, value : datetime):
        self._joined_at = value
        self.set_field_value(NodeMeshMembership.JOINED_AT, value)

    @property
    def last_seen(self):
        """Timestamp of last known device activity in this mesh."""
        return self._last_seen

    @last_seen.setter
    def last_seen(self, value : datetime):
        self._last_seen = value
        self.set_field_value(NodeMeshMembership.LAST_SEEN, value)

    def __hash__(self):
        return hash((self.mesh_id, self.device_id))

    def __str__(self):
        return f'[{self.mesh_id},{self.device_id}]: {self.mesh_roles}'

    def __repr__(self) -> str:
        return f'[{self.mesh_id},{self.device_id}]: {self.mesh_roles}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMeshMembership.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMeshMembership.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return  NodeMeshMembership.FIELD_TYPES

@dataclass(eq = False)
class NodeMesh(BaseDataModel):

    class Status(Enum):
        """Current health state of the mesh"""
        UNKNOWN     = 0
        """Need more data to make determination"""
        MINIMAL     = 1
        """Not enough nodes for quarum"""
        QUORUM      = 2
        """Mesh is fully operational"""
        CALIBRATION = 3
        """Mesh is still obtaining quorum; not yet fully operational"""

    ID              = "id"
    NAME            = "name"
    STATUS          = "status"
    DESCRIPTION     = "description"
    API_VERSION     = "api_version"

    EXPECTED_FIELDS = { ID : str, NAME : str, DESCRIPTION : str, API_VERSION: str, STATUS : int }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        ID : UUID,
        NAME: str,
        STATUS : Status,
        DESCRIPTION: str,
        API_VERSION: Version
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID                         = self._data[NodeMesh.ID]
        self._name : str                        = self._data[NodeMesh.NAME]
        self._status : NodeMesh.Status          = self._data[NodeMesh.STATUS]
        self._description : str                 = self._data[NodeMesh.DESCRIPTION]
        self._api_version : Version             = self._data[NodeMesh.API_VERSION]

    @property
    def id(self):
        """Mesh Unique Identifier"""
        return self._id

    @id.setter
    def id(self, value : UUID):
        self._id = value
        self.set_field_value(NodeMesh.ID, value)

    @property
    def name(self):
        """Mesh human readable name"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(NodeMesh.NAME, value)

    @property
    def status(self):
        """Last known status"""
        return self._status

    @status.setter
    def status(self, value : Status):
        self._status = value
        self.set_field_value(NodeMesh.STATUS, value)

    @property
    def description(self):
        """Mesh descriptor"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(NodeMesh.DESCRIPTION, value)

    @property
    def api_version(self):
        """Tome API version utilized by the mesh"""
        return self._api_version

    @api_version.setter
    def api_version(self, value : Version):
        self._api_version = value
        self.set_field_value(NodeMesh.API_VERSION, value)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.name if self.name else ""

    def __repr__(self) -> str:
        return f'{self.name},{self.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMesh.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMesh.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return  NodeMesh.FIELD_TYPES