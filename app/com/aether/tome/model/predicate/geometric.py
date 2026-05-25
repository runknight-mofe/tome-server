from dataclasses import dataclass
from typing import Type

from com.aether.tome.model.predicate.base import Predicate
from com.runknight.math.geometry import Vector3

@dataclass(eq = False)
class Point(Predicate):
    """Object model for a Line geometric predicate."""

    LOCATION       = "location"

    EXPECTED_FIELDS = { LOCATION : dict } | Predicate.EXPECTED_FIELDS
    OPTIONAL_FIELDS = { } | Predicate.OPTIONAL_FIELDS
    FIELD_TYPES = { LOCATION : Vector3, } | Predicate.FIELD_TYPES

    def __init__(self, params):
        super().__init__(params | {
            Predicate.FAMILY : Predicate.Family.GEOMETRIC,
            Predicate.TYPE : Predicate.PredicateType.POINT,
        })
        self._location : Vector3     = self._data[Point.LOCATION]

    @property
    def location(self):
        """Point location"""
        return self._location

    @location.setter
    def location(self, value : Vector3):
        self._location = value
        self.set_field_value(Point.LOCATION, value)

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Point.EXPECTED_FIELDS 

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Point.OPTIONAL_FIELDS 

    @classmethod
    def get_field_types(cls):
        return  Predicate.FIELD_TYPES | Point.FIELD_TYPES


@dataclass(eq = False)
class LineSegment(Predicate):
    """Object model for a Line geometric predicate."""

    START       = "start"
    END         = "end"

    EXPECTED_FIELDS = { START : dict, END : dict } | Predicate.EXPECTED_FIELDS
    OPTIONAL_FIELDS = { } | Predicate.OPTIONAL_FIELDS
    FIELD_TYPES = { 
        START : Vector3,
        END : Vector3,
    } | Predicate.FIELD_TYPES

    def __init__(self, params):
        super().__init__(params | {
            Predicate.FAMILY : Predicate.Family.GEOMETRIC,
            Predicate.TYPE : Predicate.PredicateType.LINE_SEGMENT,
        })
        self._start : Vector3        = self._data[LineSegment.START]
        self._end : Vector3          = self._data[LineSegment.END]

    @property
    def start(self):
        """Segment start point"""
        return self._start

    @start.setter
    def start(self, value : Vector3):
        self._start = value
        self.set_field_value(LineSegment.START, value)


    @property
    def end(self):
        """Segment end point"""
        return self._end

    @end.setter
    def end(self, value : Vector3):
        self._end = value
        self.set_field_value(LineSegment.END, value)

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return LineSegment.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return LineSegment.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return  Predicate.FIELD_TYPES | LineSegment.FIELD_TYPES

@dataclass(eq = False)
class Plane(Predicate):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    NORMAL      = "normal"

    EXPECTED_FIELDS = { POINT : dict, NORMAL : dict } | Predicate.EXPECTED_FIELDS
    OPTIONAL_FIELDS = { } | Predicate.OPTIONAL_FIELDS
    FIELD_TYPES = { 
        POINT : Vector3,
        NORMAL : Vector3
    } | Predicate.FIELD_TYPES

    def __init__(self, params):
        super().__init__(params | {
            Predicate.FAMILY : Predicate.Family.GEOMETRIC,
            Predicate.TYPE : Predicate.PredicateType.PLANE,
        })
        self._point : Vector3        = self._data[Plane.POINT]
        self._normal : Vector3       = self._data[Plane.NORMAL]

    @property
    def point(self):
        """Location on the XY plane"""
        return self._point

    @point.setter
    def point(self, value : Vector3):
        self._point = value
        self.set_field_value(Plane.POINT, value)

    @property
    def normal(self):
        """Vector3 normal to XY Plane"""
        return self._normal

    @normal.setter
    def normal(self, value : Vector3):
        self._normal = value
        self.set_field_value(Plane.NORMAL, value)


    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Plane.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Plane.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return  Predicate.FIELD_TYPES | Plane.FIELD_TYPES
    
    
@dataclass(eq = False)
class Sphere(Predicate):
    """Object model for a Plane geometric predicate."""

    POINT       = "point"
    RADIUS      = "radius"

    EXPECTED_FIELDS = { POINT : dict, RADIUS : float } | Predicate.EXPECTED_FIELDS
    OPTIONAL_FIELDS = { } | Predicate.OPTIONAL_FIELDS
    FIELD_TYPES = { 
        POINT : Vector3,
        RADIUS : float
    } | Predicate.FIELD_TYPES

    def __init__(self, params):
        super().__init__(params | {
            Predicate.FAMILY : Predicate.Family.GEOMETRIC,
            Predicate.TYPE : Predicate.PredicateType.SPHERE,
        })
        self._point : Vector3        = self._data[Sphere.POINT]
        self._radius : float        = self._data[Sphere.RADIUS]

    @property
    def point(self):
        """Center point"""
        return self._point

    @point.setter
    def point(self, value : Vector3):
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
        return Sphere.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Sphere.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return Predicate.FIELD_TYPES | Sphere.FIELD_TYPES
    
@dataclass(eq = False)
class Box(Predicate):
    """Object model for a Plane geometric predicate."""

    MIN_EXTENT  = "min_extent"
    MAX_EXTENT  = "max_extent"

    EXPECTED_FIELDS = { MIN_EXTENT : dict, MAX_EXTENT : dict } | Predicate.EXPECTED_FIELDS
    OPTIONAL_FIELDS = { } | Predicate.OPTIONAL_FIELDS
    FIELD_TYPES = { 
        MIN_EXTENT : Vector3,
        MAX_EXTENT: Vector3,
    } | Predicate.FIELD_TYPES

    def __init__(self, params):
        super().__init__(params | {
            Predicate.FAMILY : Predicate.Family.GEOMETRIC,
            Predicate.TYPE : Predicate.PredicateType.BOX,
        })
        self._min_extent : Vector3   = self._data[Box.MIN_EXTENT]
        self._max_extent : Vector3   = self._data[Box.MAX_EXTENT]

    @property
    def min_extent(self):
        """Min bound"""
        return self._min_extent

    @min_extent.setter
    def point(self, value : Vector3):
        self._min_extent = value
        self.set_field_value(Box.MIN_EXTENT, value)

    @property
    def max_extent(self):
        """Max bound"""
        return self._max_extent

    @max_extent.setter
    def max_extent(self, value : Vector3):
        self._max_extent = value
        self.set_field_value(Box.MAX_EXTENT, value)

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return Box.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return Box.OPTIONAL_FIELDS

    @classmethod
    def get_field_types(cls):
        return Predicate.FIELD_TYPES | Box.FIELD_TYPES