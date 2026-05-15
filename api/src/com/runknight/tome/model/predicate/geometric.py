from dataclasses import dataclass
from typing import Type
from vector3d.vector import Vector

from .metadata import Metadata

from ..base_model import BaseDataModel

class Predicate(BaseDataModel):
    """Tagging class defining the base predicate type"""

@dataclass(eq = False)
class Point(Predicate):
    """Object model for a Line geometric predicate."""

    LOCATION       = "location"
    METADATA       = "metadata"

    EXPECTED_FIELDS = { LOCATION : dict, METADATA: dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        LOCATION : Vector,
        METADATA : Metadata
    }

    def __init__(self, params):
        super().__init__(params)
        self._location : Vector     = self._data[Point.LOCATION]
        self._metadata : Metadata   = self._data[Point.METADATA]

    @property
    def location(self):
        """Point location"""
        return self._location

    @location.setter
    def location(self, value : Vector):
        self._location = value
        self.set_field_value(Point.LOCATION, value)

    @property
    def metadata(self):
        """Point metadata"""
        return self._metadata

    @metadata.setter
    def metadata(self, value : Metadata):
        self._metadata = value
        self.set_field_value(Point.METADATA, value)

    def __hash__(self):
        return hash(self.metadata.id)

    def __str__(self):
        return self.metadata.name if self.metadata.name else ""

    def __repr__(self) -> str:
        return f'{self.metadata.name},{self.metadata.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Point.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Point.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Point.FIELD_TYPES


@dataclass(eq = False)
class LineSegment(Predicate):
    """Object model for a Line geometric predicate."""

    START       = "start"
    END         = "end"
    METADATA    = "metadata"

    EXPECTED_FIELDS = { START : dict, END : dict, METADATA : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        START : Vector,
        END : Vector,
        METADATA: Metadata
    }

    def __init__(self, params):
        super().__init__(params)
        self._start : Vector        = self._data[LineSegment.START]
        self._end : Vector          = self._data[LineSegment.END]
        self._metadata: Metadata    = self._data[LineSegment.METADATA]

    @property
    def start(self):
        """Segment start point"""
        return self._start

    @start.setter
    def start(self, value : Vector):
        self._start = value
        self.set_field_value(LineSegment.START, value)


    @property
    def end(self):
        """Segment end point"""
        return self._end

    @end.setter
    def end(self, value : Vector):
        self._end = value
        self.set_field_value(LineSegment.END, value)

    @property
    def metadata(self):
        """Segment metadata"""
        return self._metadata

    @metadata.setter
    def metadata(self, value : Metadata):
        self._metadata = value
        self.set_field_value(LineSegment.METADATA, value)

    def __hash__(self):
        return hash(self.metadata.id)

    def __str__(self):
        return self.metadata.name if self.metadata.name else ""

    def __repr__(self) -> str:
        return f'{self.metadata.name},{self.metadata.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return LineSegment.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return LineSegment.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  LineSegment.FIELD_TYPES
    
@dataclass(eq = False)
class Plane(Predicate):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    NORMAL      = "normal"
    METADATA    = "metadata"

    EXPECTED_FIELDS = { POINT : dict, NORMAL : dict, METADATA : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        POINT : Vector,
        METADATA: Metadata,
        NORMAL : Vector
    }

    def __init__(self, params):
        super().__init__(params)
        self._point : Vector        = self._data[Plane.POINT]
        self._normal : Vector       = self._data[Plane.NORMAL]
        self._metadata: Metadata    = self._data[Plane.METADATA]

    @property
    def point(self):
        """Location on the XY plane"""
        return self._point

    @point.setter
    def point(self, value : Vector):
        self._point = value
        self.set_field_value(Plane.POINT, value)

    @property
    def normal(self):
        """Vector normal to XY Plane"""
        return self._normal

    @normal.setter
    def normal(self, value : Vector):
        self._normal = value
        self.set_field_value(Plane.NORMAL, value)

    @property
    def metadata(self):
        """Plane metadata"""
        return self._metadata

    @metadata.setter
    def metadata(self, value : Metadata):
        self._metadata = value
        self.set_field_value(Plane.METADATA, value)

    def __hash__(self):
        return hash(self.metadata.id)

    def __str__(self):
        return self.metadata.name if self.metadata.name else ""

    def __repr__(self) -> str:
        return f'{self.metadata.name},{self.metadata.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Plane.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Plane.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Plane.FIELD_TYPES
    
    
@dataclass(eq = False)
class Sphere(BaseDataModel):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    RADIUS      = "radius"
    METADATA    = "metadata"

    EXPECTED_FIELDS = { POINT : dict, RADIUS : float, METADATA : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        POINT : Vector,
        METADATA: Metadata,
        RADIUS : float
    }

    def __init__(self, params):
        super().__init__(params)
        self._point : Vector        = self._data[Sphere.POINT]
        self._radius : float        = self._data[Sphere.RADIUS]
        self._metadata: Metadata    = self._data[Sphere.METADATA]

    @property
    def point(self):
        """Center point"""
        return self._point

    @point.setter
    def point(self, value : Vector):
        self._point = value
        self.set_field_value(Sphere.POINT, value)

    @property
    def radius(self):
        """Radius"""
        return self._radius

    @radius.setter
    def radius(self, value : float):
        self._radius = value
        self.set_field_value(Sphere.RADIUS, value)

    @property
    def metadata(self):
        """Plane metadata"""
        return self._metadata

    @metadata.setter
    def metadata(self, value : Metadata):
        self._metadata = value
        self.set_field_value(Sphere.METADATA, value)

    def __hash__(self):
        return hash(self.metadata.id)

    def __str__(self):
        return self.metadata.name if self.metadata.name else ""

    def __repr__(self) -> str:
        return f'{self.metadata.name},{self.metadata.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Sphere.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Sphere.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Sphere.FIELD_TYPES
    
@dataclass(eq = False)
class Box(BaseDataModel):
    """Object model for a Plane geometric predicate."""

    MIN_EXTENT  = "min_extent"
    MAX_EXTENT  = "max_extent"
    METADATA    = "metadata"

    EXPECTED_FIELDS = { MIN_EXTENT : dict, MAX_EXTENT : dict, METADATA : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        MIN_EXTENT : Vector,
        MAX_EXTENT: Vector,
        METADATA : Metadata
    }

    def __init__(self, params):
        super().__init__(params)
        self._min_extent : Vector   = self._data[Box.MIN_EXTENT]
        self._max_extent : Vector   = self._data[Box.MAX_EXTENT]
        self._metadata: Metadata    = self._data[Box.METADATA]

    @property
    def min_extent(self):
        """Min bound"""
        return self._min_extent

    @min_extent.setter
    def point(self, value : Vector):
        self._min_extent = value
        self.set_field_value(Box.MIN_EXTENT, value)

    @property
    def max_extent(self):
        """Max bound"""
        return self._max_extent

    @max_extent.setter
    def max_extent(self, value : Vector):
        self._max_extent = value
        self.set_field_value(Box.MAX_EXTENT, value)

    @property
    def metadata(self):
        """Plane metadata"""
        return self._metadata

    @metadata.setter
    def metadata(self, value : Metadata):
        self._metadata = value
        self.set_field_value(Box.METADATA, value)

    def __hash__(self):
        return hash(self.metadata.id)

    def __str__(self):
        return self.metadata.name if self.metadata.name else ""

    def __repr__(self) -> str:
        return f'{self.metadata.name},{self.metadata.id}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Box.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Box.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Box.FIELD_TYPES