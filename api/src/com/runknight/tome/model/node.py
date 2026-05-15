from dataclasses import dataclass
from typing import Type
from uuid import UUID

from .base_model import BaseDataModel


@dataclass(eq = False)
class DeviceType(BaseDataModel):
    """Enumeration for known device types"""

    NAME            = "name"
    DESCRIPTION     = "description"
    ORDINAL         = "ordinal"

    EXPECTED_FIELDS = { NAME : str, ORDINAL : int }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        NAME : str,
        DESCRIPTION : str,
        ORDINAL : int
    }

    def __init__(self, params):
        super().__init__(params)
        self._name : str        = self._data[DeviceType.NAME]
        self._description : str = self._data[DeviceType.DESCRIPTION]
        self._ordinal : int     = self._data[DeviceType.ORDINAL]

    @property
    def name(self):
        """Device type name"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(DeviceType.NAME, value)

    @property
    def description(self):
        """Type descriptor"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(DeviceType.DESCRIPTION, value)

    @property
    def ordinal(self):
        """Type ordinal"""
        return self._ordinal

    @ordinal.setter
    def ordinal(self, value : int):
        self._ordinal = value
        self.set_field_value(DeviceType.ORDINAL, value)

    def __hash__(self):
        return hash(self.ordinal)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self) -> str:
        return f'{self.ordinal},{self.name}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return DeviceType.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return DeviceType.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  DeviceType.FIELD_TYPES


@dataclass(eq = False)
class NodeDevice(BaseDataModel):
    """Data model for a Topology Mesh Node."""

    ID                      = "id"
    TYPE                    = "type"
    IS_EMULATED             = "is_emulated"

    EXPECTED_FIELDS = { ID : str, TYPE: dict, IS_EMULATED : bool }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        ID : UUID,
        TYPE : DeviceType,
        IS_EMULATED : bool
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID         = self._data[NodeDevice.ID]
        self._type : DeviceType = self._data[NodeDevice.TYPE]
        self._is_emulated : bool = self._data[NodeDevice.IS_EMULATED]


    @property
    def id(self):
        """Node unique identifier"""
        return self._id

    @id.setter
    def id(self, value : UUID):
        self._id = value
        self.set_field_value(NodeDevice.ID, value)

    @property
    def type(self):
        """Node device type"""
        return self._type

    @type.setter
    def type(self, value : DeviceType):
        self._type = value
        self.set_field_value(NodeDevice.TYPE, value)

    @property
    def is_emulated(self):
        """Is the device emulated?"""
        return self._is_emulated

    @is_emulated.setter
    def is_emulated(self, value : bool):
        self._is_emulated = value
        self.set_field_value(NodeDevice.IS_EMULATED, value)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f'{self.id}:{self.type}'

    def __repr__(self) -> str:
        return f'{self.id}:{self.type}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return NodeDevice.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return NodeDevice.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  NodeDevice.FIELD_TYPES