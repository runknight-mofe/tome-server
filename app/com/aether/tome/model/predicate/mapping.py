from typing import Type

from com.aether.tome.model.predicate.base import Predicate
from com.aether.tome.model.predicate.geometric import Box, LineSegment, Plane, Point, Sphere

behavioral : dict[Predicate.PredicateType, Type[Predicate]] = {

}
"""Mapping of all enumerated Behavioral predicate types to their data classes"""

geometric : dict[Predicate.PredicateType, Type[Predicate]] = {
    Predicate.PredicateType.POINT : Point,
    Predicate.PredicateType.LINE_SEGMENT : LineSegment,
    Predicate.PredicateType.PLANE : Plane,
    Predicate.PredicateType.SPHERE : Sphere,
    Predicate.PredicateType.BOX : Box
}
"""Mapping of all enumerated Geometric predicate types to their data classes"""

all = behavioral | geometric
"""Mapping of all enumerated predicate types to their data class"""

def get_predicate_class_for_type(pred_type: Predicate.PredicateType): 
    return all[pred_type]