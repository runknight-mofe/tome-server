from datetime import datetime
from typing import override

from marshmallow import Schema, ValidationError, fields, post_load

from com.aether.tome.model.predicate.mapping import get_predicate_class_for_type
from com.aether.tome.model.predicate.base import Predicate
from com.runknight.schema.base import BaseSchema

class CreatePredicateSchema(BaseSchema[Predicate]):
    """Schema for creating a new predicate.

    Validates the common base fields; geometry fields for the specific subtype
    pass through without schema-level validation and are checked by the model.
    """

    __model__=  Predicate

    id                  = fields.UUID(data_key=Predicate.ID,                load_default=None,              required=False)
    name                = fields.Str(data_key=Predicate.NAME,                                               required=True)
    predicate_family    = fields.Int(data_key=Predicate.FAMILY,                                             required=True)
    predicate_type      = fields.Int(data_key=Predicate.TYPE,                                               required=True)
    description         = fields.Str(data_key=Predicate.DESCRIPTION,        load_default=None,              required=False)
    is_active           = fields.Bool(data_key=Predicate.IS_ACTIVE,         load_default=True,              required=False)
    created_at          = fields.DateTime(data_key=Predicate.CREATED_AT,    load_default=datetime.now(),    required=False)
    modified_at          = fields.DateTime(data_key=Predicate.MODIFIED_AT,  load_default=datetime.now(),    required=False)

    @override
    def get_model_cls(self, data):
        pred_type_ord = data[Predicate.TYPE]
        if not pred_type_ord:
            raise ValidationError(f"{type(self)} failed to marshal a predicate from data; missing required data param [{Predicate.TYPE}]")
        pred_type = None
        try:
            pred_type = Predicate.PredicateType(pred_type_ord)
        except Exception as e:
            raise ValidationError(f"{type(self)} failed to marshal a predicate from data; Nonexisting type ordinal [{pred_type_ord}] provided.",e=e)

        return get_predicate_class_for_type(pred_type)

create_predicate_schema : CreatePredicateSchema = CreatePredicateSchema()