from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from packaging.version import Version
from typing import Type
from uuid import UUID

from .base_model import BaseDataModel
from .predicate.geometric import Predicate


@dataclass(eq = False)
class NodeMeshMembership(BaseDataModel):
    """Describes membership of a node within a mesh topology instance"""

    class Role(Enum):
        """Responsibility of the node within the mesh"""
        MEMBER  = 0,
        GATEWAY = 1
        ADMIN   = 2
        ROOT    = 3

    NODE_ID     = "node_id"
    MESH_ID     = "mesh_id"
    MESH_ROLES  = "mesh_roles"
    IS_ADMIN    = "is_admin"
    IS_ANCHOR   = "is_anchor"
    IS_ROOT     = "is_root"
    JOINED_AT   = "joined_at"
    LAST_SEEN   = "last_seen"

    EXPECTED_FIELDS = { NODE_ID : str, MESH_ID : str, MESH_ROLES : list, IS_ADMIN : bool, IS_ANCHOR: bool, IS_ROOT : bool, JOINED_AT : str, LAST_SEEN : str }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        MESH_ID : UUID,
        NODE_ID : UUID,
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
        self._node_id : UUID                                = self._data[NodeMeshMembership.NODE_ID]
        self._is_anchor : bool                              = self._data[NodeMeshMembership.IS_ANCHOR]
        self._mesh_roles : list[NodeMeshMembership.Role]    = self._data[NodeMeshMembership.MESH_ROLES]
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
    def node_id(self):
        """Member node unique identifier"""
        return self._node_id

    @node_id.setter
    def node_id(self, value : UUID):
        self._node_id = value
        self.set_field_value(NodeMeshMembership.NODE_ID, value)

    @property
    def is_anchor(self):
        """Is the node an anchor in the mesh"""
        return self._is_anchor

    @is_anchor.setter
    def is_anchor(self, value : bool):
        self._node_type = value
        self.set_field_value(NodeMeshMembership.IS_ANCHOR, value)

    @property
    def mesh_roles(self):
        """Roles for associated node within mesh"""
        return self._mesh_roles

    @mesh_roles.setter
    def mesh_roles(self, value : list[Role]):
        self._mesh_roles = value
        self.set_field_value(NodeMeshMembership.MESH_ROLES, value)

    @property
    def is_admin(self):
        """Is the node an admin of the mesh"""
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
        """Timestamp of node joining the mesh"""
        return self._joined_at

    @joined_at.setter
    def joined_at(self, value : datetime):
        self._joined_at = value
        self.set_field_value(NodeMeshMembership.JOINED_AT, value)

    @property
    def last_seen(self):
        """Timestamp of last known node activity within mesh"""
        return self._last_seen

    @last_seen.setter
    def last_seen(self, value : datetime):
        self._last_seen = value
        self.set_field_value(NodeMeshMembership.LAST_SEEN, value)

    def __hash__(self):
        return hash((self.mesh_id, self.node_id))

    def __str__(self):
        return f'[{self.mesh_id},{self.node_id}]: {self.mesh_roles}'

    def __repr__(self) -> str:
        return f'[{self.mesh_id},{self.node_id}]: {self.mesh_roles}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeMeshMembership.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeMeshMembership.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  NodeMeshMembership.FIELD_TYPES


@dataclass(eq = False)
class NodeMesh(BaseDataModel):

    class Status(Enum):
        """Current health state of the mesh"""
        UNKNOWN     = 0,
        """Need more data to make determination"""
        MINIMAL     = 1,
        """Not enough nodes for quarum"""
        QUORUM      = 2,
        """Mesh is fully operational"""
        CALIBRATION = 3
        """Mesh is still obtaining quorum; not yet fully operational"""

    ID              = "id"
    NAME            = "name"
    NODES           = "nodes"
    PREDICATES      = "predicates"
    STATUS          = "status"
    DESCRIPTION     = "description"
    API_VERSION     = "api_version"

    EXPECTED_FIELDS = { ID : str, NAME : str, NODES : list, PREDICATES : list, DESCRIPTION : str, API_VERSION: str, STATUS : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        ID : UUID,
        NAME: str,
        NODES : list[NodeMeshMembership],
        PREDICATES : list[Predicate],
        STATUS : Status,
        DESCRIPTION: str,
        API_VERSION: Version
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID                         = self._data[NodeMesh.ID]
        self._name : str                        = self._data[NodeMesh.NAME]
        self._nodes : list[NodeMeshMembership]  = self._data[NodeMesh.NODES]
        self._predicates : list[Predicate]      = self._data[NodeMesh.PREDICATES]
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
    def nodes(self):
        """Node members of the mesh"""
        return self._nodes

    @nodes.setter
    def nodes(self, value : list[NodeMeshMembership]):
        self._nodes = value
        self.set_field_value(NodeMesh.NODES, value)

    @property
    def predicates(self):
        """Predicates owned by the mesh"""
        return self._predicates

    @predicates.setter
    def predicates(self, value : list[Predicate]):
        self._predicates = value
        self.set_field_value(NodeMesh.PREDICATES, value)

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

    @staticmethod
    def get_field_types():
        return  NodeMesh.FIELD_TYPES