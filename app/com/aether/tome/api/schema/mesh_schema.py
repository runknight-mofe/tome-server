from typing import Generic, Type, TypeVar
from marshmallow import Schema, fields, post_load, validate
from com.aether.tome.model.mesh import NodeMeshMembership
from com.aether.tome.model.request import NodeMeshMembershipRequest, NodeMeshPredicateMembershipRequest
T = TypeVar('T')

class BaseSchema(Schema, Generic[T]):
    
    __model__ : Type[T]

    def load_data(self, data) -> T:
        obj =  self.load(data)
        if not isinstance(obj, self.__model__):
            raise TypeError(
                f"Deserialized object is not of type {self.__model__.__name__}; got {type(obj)}"
            )
        return obj
        
    @post_load
    def post_load(self, data, **kwargs) -> T:
        return self.__model__(data) # type: ignore


class MeshMembershipSchema(BaseSchema[NodeMeshMembershipRequest]):
    """Schema for device joining an existing node mesh
    
    Validates request for a device joining a node mesh
    """

    __model__ = NodeMeshMembershipRequest
    """Object type whose data is being validated"""

    device_id = fields.UUID(
        data_key = NodeMeshMembershipRequest.DEVICE_ID,
        required = True,
    )
    """Device joining the mesh"""

    mesh_id = fields.UUID(
        data_key = NodeMeshMembershipRequest.MESH_ID,
        required = True,
    )
    """Existing node mesh"""

    roles = fields.List(
        fields.Enum(NodeMeshMembership.Role),
        data_key = NodeMeshMembershipRequest.ROLES,
        required = True,
        allow_none = False,
        validate = validate.Length(
            min = 1
        )
    )
    """Roles being requested by the joining device"""

mesh_membership_schema : MeshMembershipSchema = MeshMembershipSchema()


class MeshPredicateMembershipSchema(BaseSchema[NodeMeshPredicateMembershipRequest]):
    """Schema for associating an existing predicate with a node mesh."""

    __model__ = NodeMeshPredicateMembershipRequest

    predicate_id = fields.UUID(
        data_key = NodeMeshPredicateMembershipRequest.PREDICATE_ID,
        required = True,
    )
    """Predicate to associate with the mesh"""

    mesh_id = fields.UUID(
        data_key = NodeMeshPredicateMembershipRequest.MESH_ID,
        required = True,
    )
    """Existing node mesh"""

    position = fields.Int(
        data_key = NodeMeshPredicateMembershipRequest.POSITION,
        load_default = 0,
    )
    """Ordered position of the predicate within the mesh"""

mesh_predicate_membership_schema : MeshPredicateMembershipSchema = MeshPredicateMembershipSchema()