from marshmallow import fields, validate

from com.runknight.schema.base import BaseSchema
from com.aether.tome.model.user import User, UserSession
from com.aether.tome.model.request import UserSessionRequest


class CreateUserSchema(BaseSchema[User]):
    """Validates a request to register or retrieve a user."""

    __model__ = User

    username = fields.Str(
        data_key    = User.USERNAME,
        required    = True,
        validate    = validate.Length(min=1),
    )
    display_name = fields.Str(
        data_key    = User.DISPLAY_NAME,
        load_default = None,
        required    = False,
    )


create_user_schema: CreateUserSchema = CreateUserSchema()


class CreateUserSessionSchema(BaseSchema[UserSessionRequest]):
    """Validates a request to establish a user session on a device."""

    __model__ = UserSessionRequest

    user_id = fields.UUID(
        data_key = UserSessionRequest.USER_ID,
        required = True,
    )
    device_id = fields.UUID(
        data_key = UserSessionRequest.DEVICE_ID,
        required = True,
    )
    duration_hours = fields.Int(
        data_key     = UserSessionRequest.DURATION_HOURS,
        load_default = 24,
        required     = False,
        validate     = validate.Range(min=1, max=720),
    )


create_user_session_schema: CreateUserSessionSchema = CreateUserSessionSchema()
