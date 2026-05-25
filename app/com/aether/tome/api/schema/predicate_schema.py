from marshmallow import Schema, fields, post_load, INCLUDE

from com.aether.tome.model.predicate.base import Predicate
from com.aether.tome.model.predicate.geometric import Box, LineSegment, Plane, Point, Sphere

_TYPE_MAP = {
    Predicate.PredicateType.POINT        : Point,
    Predicate.PredicateType.LINE_SEGMENT : LineSegment,
    Predicate.PredicateType.PLANE        : Plane,
    Predicate.PredicateType.SPHERE       : Sphere,
    Predicate.PredicateType.BOX          : Box,
}


class CreatePredicateSchema(Schema):
    """Schema for creating a new predicate.

    Validates the common base fields; geometry fields for the specific subtype
    pass through without schema-level validation and are checked by the model.
    """

    class Meta:
        unknown = INCLUDE

    name             = fields.Str(data_key=Predicate.NAME,   required=True)
    predicate_family = fields.Int(data_key=Predicate.FAMILY, required=True)
    predicate_type   = fields.Int(data_key=Predicate.TYPE,   required=True)
    description      = fields.Str(data_key=Predicate.DESCRIPTION, load_default=None)
    is_active        = fields.Bool(data_key=Predicate.IS_ACTIVE,   load_default=True)

    @post_load
    def post_load(self, data, **kwargs):
        data.setdefault(Predicate.ID,          None)
        data.setdefault(Predicate.CREATED_AT,  None)
        data.setdefault(Predicate.MODIFIED_AT, None)
        pred_type = Predicate.PredicateType(data[Predicate.TYPE])
        cls = _TYPE_MAP.get(pred_type, Predicate)
        return cls(data)


create_predicate_schema : CreatePredicateSchema = CreatePredicateSchema()
