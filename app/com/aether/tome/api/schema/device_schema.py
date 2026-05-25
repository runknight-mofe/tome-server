
from typing import Generic, Type, TypeVar
from marshmallow import Schema, fields, post_load, validate
from com.aether.tome.model.device import Device
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


class CreateDeviceRequestSchema(BaseSchema[Device]):
    """Schema for a device
    
    Validates data object for a device
    """

    __model__ = Device
    """Object type whose data is being validated"""

    id = fields.UUID(
        data_key = Device.ID,
        required = False,
    )
    """Device unique identifier"""

    name = fields.Str(
        data_key = Device.NAME,
        required = True,
        validate = validate.Length(min = 1)
    )
    """Human readable name"""

    description = fields.Str(
        data_key = Device.DESCRIPTION,
        required = False,
        validate = validate.Length(min = 1)
    )
    """Human readable description"""

    type = fields.Int(
        data_key = Device.TYPE,
        required = True,
        validate = validate.Range(min=0, max=900, min_inclusive=True,max_inclusive=True)
    )
    """physical device type"""

    is_active = fields.Bool(
        data_key = Device.IS_ACTIVE,
        required = False
    )
    """Is device active?"""

    is_emulated = fields.Bool(
        data_key = Device.IS_EMULATED,
        required = True
    )
    """Is device not physical?"""

    created_at = fields.DateTime(
        data_key = Device.CREATED_AT,
        required = False
    )
    """Is device not physical?"""

device_create_req_schema : CreateDeviceRequestSchema = CreateDeviceRequestSchema()