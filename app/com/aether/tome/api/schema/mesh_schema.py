from com.runknight.schema.base import BaseSchema, BaseUpdateRequestSchema, VersionField
from marshmallow import fields, validate
from packaging.version import Version
from com.aether.tome.model.mesh import NodeMesh, NodeMeshMembership
from com.aether.tome.model.request import NodeMeshMembershipRequest, NodeMeshPredicateMembershipRequest


class CreateMeshRequestSchema(BaseSchema[NodeMesh]):
    """Schema for schema creation request; 
    
    Validates a request to create a new node mesh
    """
    __model__ = NodeMesh
    """Object type whose data is being validated"""

    ID              = "id"
    NAME            = "name"
    STATUS          = "status"
    DESCRIPTION     = "description"
    API_VERSION     = "api_version"

    id = fields.UUID(           data_key = NodeMesh.ID,             load_default=None,                      required = False)
    """Existing node mesh"""
    name = fields.Str(          data_key = NodeMesh.NAME,                                                   required = True, validate=validate.Length(min=1))
    """Human readable name of the mesh"""
    status = fields.Enum(       data_key = NodeMesh.STATUS,         load_default=NodeMesh.Status.UNKNOWN,   required = False, enum=NodeMesh.Status,by_value = True)
    """Initial state of the created mesh"""
    description = fields.Str(   data_key = NodeMesh.DESCRIPTION,                                            required = True, validate=validate.Length(min=1))
    """Human readable description for the mesh"""
    api_version = VersionField( data_key = NodeMesh.API_VERSION,                                            required = True)
    """Valid api version string"""

create_mesh_request_schema : CreateMeshRequestSchema = CreateMeshRequestSchema()

class UpdateMeshRequestSchema(BaseUpdateRequestSchema[NodeMesh]):
    """Schema for schema update request; 
    
    Validates a request to create a new node mesh
    """

    __data_model__ = NodeMesh
    """Object update mappings"""

update_mesh_request_schema : UpdateMeshRequestSchema = UpdateMeshRequestSchema()


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