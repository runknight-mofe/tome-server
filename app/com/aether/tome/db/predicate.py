from typing import Any

from com.aether.tome.model.predicate.geometric import Box, LineSegment, Plane, Point, Sphere
from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.predicate.base import Predicate

# ---------------------------------------------------------------------------
# PredicateRepo
# Keys: [ID]
# ---------------------------------------------------------------------------
class PredicateRepo(BaseRepository[Predicate]):
    """Repository for all predicates."""
 
    __model__ = Predicate

    TYPE_MAP = {
        Predicate.PredicateType.POINT : Point,
        Predicate.PredicateType.LINE_SEGMENT : LineSegment,
        Predicate.PredicateType.PLANE : Plane,
        Predicate.PredicateType.SPHERE : Sphere,
        Predicate.PredicateType.BOX : Box,
    }

    KEYS = [Predicate.ID, Predicate.NAME]
 
    def __init__(self, db: DBConnector | None = None,db_params: dict | None = None):
        super().__init__(PredicateRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_predicates"
        self.sql[self.ADD]    = "add_many_predicates"
        self.sql[self.UPDATE] = "update_many_predicates"
        self.sql[self.REMOVE] = "remove_many_predicates"

    def get_model(self, data: dict[str, Any] | None = None):
        """Overrides default data model type for specifying the specififc predicate type; used when deserializing"""

        if data and Predicate.TYPE in data and Predicate.PredicateType(data[Predicate.TYPE]) in self.TYPE_MAP:
            return self.TYPE_MAP[Predicate.PredicateType(data[Predicate.TYPE])]

        return super().get_model(data)