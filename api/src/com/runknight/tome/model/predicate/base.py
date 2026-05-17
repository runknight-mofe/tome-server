from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from com.runknight.model.base_model import BaseDataModel

@dataclass
class Predicate(BaseDataModel):
    """Tagging class defining the base predicate type"""

    ID          = "id"
    NAME        = "name"
    IS_ACTIVE   = "is_active"
    CREATED_AT  = "created_at"
    MODIFIED_AT = "modified_at"
    DESCRIPTION = "description"
    FAMILY      = "predicate_family"
    TYPE        = "predicate_type"

    class Family(Enum):
        """Major predicate type categories"""

        GEOMETRIC = 0
        """Spatial predicates such as points, lines, and spheres"""
        BEHAVIOR = 1
        """HITL based predicates like waving, walking or other forms of motion"""
        RANGING = 2
        """Pertaining to the node device itself"""

    class PredicateType(Enum):
        """Discrete predicate data types"""
        #----------------------------------------------------------------------
        # Geometric predicate types
        #----------------------------------------------------------------------
        POINT = 0
        """Single point"""
        LINE_SEGMENT = 1
        """Two points"""
        PLANE = 2
        """XY Plane + orthoganal vector"""
        SPHERE = 3
        """Center point + radius"""
        BOX = 4
        """Two points defining a min and max extent of a rectangular prism"""
        #----------------------------------------------------------------------
        # Behavioral predicate types
        #----------------------------------------------------------------------
        # TBD
        
        #----------------------------------------------------------------------
        # Ranging predicate types
        #----------------------------------------------------------------------
        # TBD

    DEFAULT_DESCRIPTION = ""

    EXPECTED_FIELDS = {
        ID : str,
        NAME : str,
        IS_ACTIVE: bool,
        CREATED_AT : str,
        MODIFIED_AT : str,
        FAMILY : int,
        TYPE : int 
    }
    OPTIONAL_FIELDS = { DESCRIPTION: str }

    FIELD_TYPES = {
        ID : UUID,
        CREATED_AT : datetime,
        DESCRIPTION: str,
        IS_ACTIVE : bool,
        MODIFIED_AT : datetime,
        NAME : str,
        FAMILY : Family,
        TYPE: PredicateType,
    }

    def __init__(self, params):
        super().__init__(params)
        self._id : UUID                         = self._data[Predicate.ID]
        self._name : str                        = self._data[Predicate.NAME]
        self._description : str                 = self._data[Predicate.DESCRIPTION] if Predicate.DESCRIPTION in self._data else Predicate.DEFAULT_DESCRIPTION
        self._is_active : bool                  = self._data[Predicate.IS_ACTIVE]
        self._created_at : datetime             = self._data[Predicate.CREATED_AT]
        self._modified_at : datetime            = self._data[Predicate.MODIFIED_AT]
        self._family : Predicate.Family         = self._data[Predicate.FAMILY]
        self._type : Predicate.PredicateType    = self._data[Predicate.TYPE]
    
    @property
    def id(self):
        """Unique identifier"""
        return self._id

    @id.setter
    def id(self, value : UUID):
        self._id = value
        self.set_field_value(Predicate.ID, value)
    
    @property
    def name(self):
        """Human readable identifier for the predicate"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(Predicate.NAME, value)
        
    @property
    def description(self):
        """String descriptor for the predicate"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(Predicate.DESCRIPTION, value)
        
    @property
    def is_active(self):
        """Flag signifying active status for predicate"""
        return self._is_active

    @is_active.setter
    def is_active(self, value : bool):
        self._is_active = value
        self.set_field_value(Predicate.IS_ACTIVE, value)
        
    @property
    def created_at(self):
        """Creation timestamp"""
        return self._created_at

    @created_at.setter
    def created_at(self, value : datetime):
        self._created_at = value
        self.set_field_value(Predicate.CREATED_AT, value)
        
    @property
    def modified_at(self):
        """Last modification timestamp"""
        return self._created_at

    @modified_at.setter
    def modified_at(self, value : datetime):
        self._modified_at = value
        self.set_field_value(Predicate.MODIFIED_AT, value)

    @property
    def family(self):
        """General category"""
        return self._family

    @family.setter
    def family(self, value : Family):
        self._family = value
        self.set_field_value(Predicate.FAMILY, value)

    @property
    def type(self):
        """Explicit type"""
        return self._type

    @type.setter
    def type(self, value : PredicateType):
        self._type = value
        self.set_field_value(Predicate.TYPE, value)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.name if self.name else ""

    def __repr__(self) -> str:
        return f'{self.name},{self.id}'