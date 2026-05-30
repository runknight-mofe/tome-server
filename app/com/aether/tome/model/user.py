from dataclasses import dataclass
from datetime import datetime
from typing import Type
from uuid import UUID, uuid4

from com.runknight.model.base_model import BaseDataModel


@dataclass(eq=False)
class User(BaseDataModel):
    """A human principal who owns devices and manages mesh operations."""

    ID           = "id"
    USERNAME     = "username"
    DISPLAY_NAME = "display_name"
    CREATED_AT   = "created_at"

    EXPECTED_FIELDS = {
        ID           : str,
        USERNAME     : str,
        DISPLAY_NAME : str,
        CREATED_AT   : str,
    }
    OPTIONAL_FIELDS = {}
    FIELD_TYPES = {
        ID           : UUID,
        USERNAME     : str,
        DISPLAY_NAME : str,
        CREATED_AT   : datetime,
    }
    DEFAULT_VALUES = {
        ID         : uuid4(),
        CREATED_AT : datetime.now(),
    }

    def __init__(self, params):
        super().__init__(params)
        self._id           : UUID     = self._data[User.ID]
        self._username     : str      = self._data[User.USERNAME]
        self._display_name : str      = self._data[User.DISPLAY_NAME]
        self._created_at   : datetime = self._data[User.CREATED_AT]

    @property
    def id(self):
        """User unique identifier"""
        return self._id

    @id.setter
    def id(self, value: UUID):
        self._id = value
        self.set_field_value(User.ID, value)

    @property
    def username(self):
        """Unique login handle, sourced from the identity provider"""
        return self._username

    @username.setter
    def username(self, value: str):
        self._username = value
        self.set_field_value(User.USERNAME, value)

    @property
    def display_name(self):
        """Human-readable name for display purposes"""
        return self._display_name

    @display_name.setter
    def display_name(self, value: str):
        self._display_name = value
        self.set_field_value(User.DISPLAY_NAME, value)

    @property
    def created_at(self):
        """Timestamp when user record was created (immutable)"""
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        self._created_at = value
        self.set_field_value(User.CREATED_AT, value)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.username if self.username else ""

    def __repr__(self) -> str:
        return f'{self.username},{self.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return User.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return User.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return User.FIELD_TYPES

    @staticmethod
    def get_default_values():
        return User.DEFAULT_VALUES


@dataclass(eq=False)
class UserSession(BaseDataModel):
    """
    Records a user's active presence on a specific device.

    A user may only hold one active session at a time (enforced by a partial
    unique index on users(user_id) WHERE is_active = TRUE).  A device may
    likewise only host one active session at a time.

    While the session is active the associated device is eligible to
    participate in meshes on behalf of that user.  When the session expires
    (via logout, inactivity, or explicit expiry) all mesh memberships backed
    by this session are dropped.
    """

    ID             = "id"
    USER_ID        = "user_id"
    DEVICE_ID      = "device_id"
    CREATED_AT     = "created_at"
    EXPIRES_AT     = "expires_at"
    LAST_ACTIVE_AT = "last_active_at"
    IS_ACTIVE      = "is_active"

    EXPECTED_FIELDS = {
        ID             : str,
        USER_ID        : str,
        DEVICE_ID      : str,
        CREATED_AT     : str,
        EXPIRES_AT     : str,
        LAST_ACTIVE_AT : str,
        IS_ACTIVE      : bool,
    }
    OPTIONAL_FIELDS = {}
    FIELD_TYPES = {
        ID             : UUID,
        USER_ID        : UUID,
        DEVICE_ID      : UUID,
        CREATED_AT     : datetime,
        EXPIRES_AT     : datetime,
        LAST_ACTIVE_AT : datetime,
        IS_ACTIVE      : bool,
    }
    DEFAULT_VALUES = {
        ID        : uuid4(),
        IS_ACTIVE : True,
    }

    def __init__(self, params):
        super().__init__(params)
        self._id             : UUID     = self._data[UserSession.ID]
        self._user_id        : UUID     = self._data[UserSession.USER_ID]
        self._device_id      : UUID     = self._data[UserSession.DEVICE_ID]
        self._created_at     : datetime = self._data[UserSession.CREATED_AT]
        self._expires_at     : datetime = self._data[UserSession.EXPIRES_AT]
        self._last_active_at : datetime = self._data[UserSession.LAST_ACTIVE_AT]
        self._is_active      : bool     = self._data[UserSession.IS_ACTIVE]

    @property
    def id(self):
        """Session unique identifier"""
        return self._id

    @id.setter
    def id(self, value: UUID):
        self._id = value
        self.set_field_value(UserSession.ID, value)

    @property
    def user_id(self):
        """ID of the user holding this session — fetch full User via UserRepo"""
        return self._user_id

    @user_id.setter
    def user_id(self, value: UUID):
        self._user_id = value
        self.set_field_value(UserSession.USER_ID, value)

    @property
    def device_id(self):
        """ID of the device this session is bound to — fetch full Device via DeviceRepo"""
        return self._device_id

    @device_id.setter
    def device_id(self, value: UUID):
        self._device_id = value
        self.set_field_value(UserSession.DEVICE_ID, value)

    @property
    def created_at(self):
        """Timestamp when the session was established (immutable)"""
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        self._created_at = value
        self.set_field_value(UserSession.CREATED_AT, value)

    @property
    def expires_at(self):
        """Hard expiry timestamp; session is invalid after this point regardless of activity"""
        return self._expires_at

    @expires_at.setter
    def expires_at(self, value: datetime):
        self._expires_at = value
        self.set_field_value(UserSession.EXPIRES_AT, value)

    @property
    def last_active_at(self):
        """Timestamp of last observed user activity through this session"""
        return self._last_active_at

    @last_active_at.setter
    def last_active_at(self, value: datetime):
        self._last_active_at = value
        self.set_field_value(UserSession.LAST_ACTIVE_AT, value)

    @property
    def is_active(self):
        """False when the user has logged out or the session has been expired"""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
        self.set_field_value(UserSession.IS_ACTIVE, value)

    def is_expired(self) -> bool:
        """True if the session is logically invalid (inactive or past expiry)."""
        from datetime import timezone
        if not self.is_active:
            return True
        if self.expires_at:
            now = datetime.now(timezone.utc)
            expires = self.expires_at
            if expires.tzinfo is None:
                from datetime import timezone as tz
                expires = expires.replace(tzinfo=tz.utc)
            if now > expires:
                return True
        return False

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f'session:{self.id} user:{self.user_id} device:{self.device_id}'

    def __repr__(self) -> str:
        return f'UserSession({self.id}, user={self.user_id}, device={self.device_id}, active={self.is_active})'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return UserSession.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return UserSession.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return UserSession.FIELD_TYPES

    @staticmethod
    def get_default_values():
        return UserSession.DEFAULT_VALUES
