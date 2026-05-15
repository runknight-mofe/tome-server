from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..base_model import BaseDataModel


@dataclass
class Metadata(BaseDataModel):
    """Defines common properties held by every predicate"""
    
    ID = "id"
    NAME = "name"
    IS_ACTIVE = "is_active"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    DESCRIPTION = "description"

    DEFAULT_DESCRIPTION = ""

    EXPECTED_FIELDS = { ID : str, NAME : str, IS_ACTIVE: bool, CREATED_AT : str, MODIFIED_AT : str }
    OPTIONAL_FIELDS = { DESCRIPTION: str }
    FIELD_TYPES = { 
        CREATED_AT : datetime,
        DESCRIPTION: str,
        ID : UUID,
        IS_ACTIVE : bool,
        MODIFIED_AT : datetime,
        NAME : str
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID                 = self._data[Metadata.ID]
        self._name : str                = self._data[Metadata.NAME]
        self._description : str         = self._data[Metadata.DESCRIPTION] if Metadata.DESCRIPTION in self._data else self.DEFAULT_DESCRIPTION
        self._is_active : bool          = self._data[Metadata.IS_ACTIVE]
        self._created_at : datetime     = self._data[Metadata.CREATED_AT]
        self._modified_at : datetime    = self._data[Metadata.MODIFIED_AT]


    @property
    def id(self):
        """Unique identifier for the predicate"""
        return self._id

    @id.setter
    def id(self, value : UUID):
        self._id = value
        self.set_field_value(Metadata.ID, value)
        
    @property
    def name(self):
        """Human readable identifier for the predicate"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(Metadata.NAME, value)
        
    @property
    def description(self):
        """String descriptor for the predicate"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(Metadata.DESCRIPTION, value)
        
    @property
    def is_active(self):
        """Flag signifying active status for predicate"""
        return self._is_active

    @is_active.setter
    def is_active(self, value : bool):
        self._is_active = value
        self.set_field_value(Metadata.IS_ACTIVE, value)
        
    @property
    def created_at(self):
        """Creation timestamp"""
        return self._created_at

    @created_at.setter
    def created_at(self, value : datetime):
        self._created_at = value
        self.set_field_value(Metadata.CREATED_AT, value)
        
    @property
    def modified_at(self):
        """Last modification timestamp"""
        return self._created_at

    @modified_at.setter
    def modified_at(self, value : datetime):
        self._modified_at = value
        self.set_field_value(Metadata.MODIFIED_AT, value)