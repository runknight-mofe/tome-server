from dataclasses import dataclass
from typing import Type
from uuid import UUID

from com.runknight.tome.model.device import DeviceType
from com.runknight.model.base_model import BaseDataModel

@dataclass(eq = False)
class Node(BaseDataModel):
    """Data model for a Topology Mesh Node."""

    ID                      = "id"
    NAME                    = "name"
    DESCRIPTION             = "description"
    TYPE                    = "type"
    IS_EMULATED             = "is_emulated"

    EXPECTED_FIELDS = { ID : str, NAME : str, DESCRIPTION : str, TYPE: dict, IS_EMULATED : bool }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        ID : UUID,
        NAME : str,
        DESCRIPTION : str,
        TYPE : DeviceType,
        IS_EMULATED : bool
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID             = self._data[Node.ID]
        self._name : str            = self._data[Node.NAME]
        self._description : str     = self._data[Node.DESCRIPTION]
        self._type : DeviceType     = self._data[Node.TYPE]
        self._is_emulated : bool    = self._data[Node.IS_EMULATED]


    @property
    def id(self):
        """Node unique identifier"""
        return self._id

    @id.setter
    def id(self, value : UUID):
        self._id = value
        self.set_field_value(Node.ID, value)

    @property
    def name(self):
        """Human readable name"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(Node.NAME, value)

    @property
    def description(self):
        """Human readable description"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(Node.DESCRIPTION, value)

    @property
    def type(self):
        """Node device type"""
        return self._type

    @type.setter
    def type(self, value : DeviceType):
        self._type = value
        self.set_field_value(Node.TYPE, value)

    @property
    def is_emulated(self):
        """Is the device emulated?"""
        return self._is_emulated

    @is_emulated.setter
    def is_emulated(self, value : bool):
        self._is_emulated = value
        self.set_field_value(Node.IS_EMULATED, value)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f'{self.id}:{self.type}'

    def __repr__(self) -> str:
        return f'{self.id}:{self.type}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Node.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Node.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Node.FIELD_TYPES