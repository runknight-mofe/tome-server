from dataclasses import dataclass
from typing import Type
from vector3d.vector import Vector

from com.runknight.tome.model.predicate.base import Predicate

@dataclass(eq = False)
class Point(Predicate):
    """Object model for a Line geometric predicate."""

    LOCATION       = "location"

    EXPECTED_FIELDS = { LOCATION : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { LOCATION : Vector, }

    def __init__(self, params):
        super().__init__(params)
        self._location : Vector     = self._data[Point.LOCATION]

    @property
    def location(self):
        """Point location"""
        return self._location

    @location.setter
    def location(self, value : Vector):
        self._location = value
        self.set_field_value(Point.LOCATION, value)

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Point.EXPECTED_FIELDS | Predicate.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Point.OPTIONAL_FIELDS | Predicate.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Point.FIELD_TYPES | Predicate.FIELD_TYPES


@dataclass(eq = False)
class LineSegment(Predicate):
    """Object model for a Line geometric predicate."""

    START       = "start"
    END         = "end"

    EXPECTED_FIELDS = { START : dict, END : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        START : Vector,
        END : Vector,
    }

    def __init__(self, params):
        super().__init__(params)
        self._start : Vector        = self._data[LineSegment.START]
        self._end : Vector          = self._data[LineSegment.END]

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

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return LineSegment.EXPECTED_FIELDS | Predicate.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return LineSegment.OPTIONAL_FIELDS | Predicate.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  LineSegment.FIELD_TYPES | Predicate.FIELD_TYPES
    
@dataclass(eq = False)
class Plane(Predicate):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    NORMAL      = "normal"

    EXPECTED_FIELDS = { POINT : dict, NORMAL : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        POINT : Vector,
        NORMAL : Vector
    }

    def __init__(self, params):
        super().__init__(params)
        self._point : Vector        = self._data[Plane.POINT]
        self._normal : Vector       = self._data[Plane.NORMAL]

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


    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Plane.EXPECTED_FIELDS | Predicate.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Plane.OPTIONAL_FIELDS | Predicate.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Plane.FIELD_TYPES | Predicate.FIELD_TYPES
    
    
@dataclass(eq = False)
class Sphere(Predicate):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    RADIUS      = "radius"

    EXPECTED_FIELDS = { POINT : dict, RADIUS : float }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        POINT : Vector,
        RADIUS : float
    }

    def __init__(self, params):
        super().__init__(params)
        self._point : Vector        = self._data[Sphere.POINT]
        self._radius : float        = self._data[Sphere.RADIUS]

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

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Sphere.EXPECTED_FIELDS | Predicate.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Sphere.OPTIONAL_FIELDS | Predicate.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Sphere.FIELD_TYPES | Predicate.FIELD_TYPES
    
@dataclass(eq = False)
class Box(Predicate):
    """Object model for a Plane geometric predicate."""

    MIN_EXTENT  = "min_extent"
    MAX_EXTENT  = "max_extent"

    EXPECTED_FIELDS = { MIN_EXTENT : dict, MAX_EXTENT : dict }
    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        MIN_EXTENT : Vector,
        MAX_EXTENT: Vector,
    }

    def __init__(self, params):
        super().__init__(params)
        self._min_extent : Vector   = self._data[Box.MIN_EXTENT]
        self._max_extent : Vector   = self._data[Box.MAX_EXTENT]

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

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Box.EXPECTED_FIELDS | Predicate.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Box.OPTIONAL_FIELDS | Predicate.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  Box.FIELD_TYPES | Predicate.FIELD_TYPES