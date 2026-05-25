from typing import Any
from uuid import UUID

from com.aether.tome.model.predicate.geometric import Box, LineSegment, Plane, Point, Sphere
from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.predicate.base import Predicate

# ---------------------------------------------------------------------------
# PredicateRepo
# Keys: [ID, NAME]
# ---------------------------------------------------------------------------
class PredicateRepo(BaseRepository[Predicate]):
    """Repository for all predicates."""

    __model__ = Predicate

    TYPE_MAP = {
        Predicate.PredicateType.POINT        : Point,
        Predicate.PredicateType.LINE_SEGMENT : LineSegment,
        Predicate.PredicateType.PLANE        : Plane,
        Predicate.PredicateType.SPHERE       : Sphere,
        Predicate.PredicateType.BOX          : Box,
    }

    KEYS = [Predicate.ID, Predicate.NAME]

    def __init__(self, db: DBConnector | None = None, db_params: dict | None = None):
        super().__init__(PredicateRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_predicates"
        self.sql[self.ADD]    = "add_many_predicates"
        self.sql[self.UPDATE] = "update_many_predicates"
        self.sql[self.REMOVE] = "remove_many_predicates"

    def get_model(self, data: dict[str, Any] | None = None):
        """Override: selects the concrete Predicate subclass based on predicate_type."""
        if data and Predicate.TYPE in data and Predicate.PredicateType(data[Predicate.TYPE]) in self.TYPE_MAP:
            return self.TYPE_MAP[Predicate.PredicateType(data[Predicate.TYPE])]
        return super().get_model(data)

    def get_active_predicates(self) -> set[Predicate]:
        """Return all predicates with is_active=True."""
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_active_predicates; repo not initialized')
        with self._lock:
            return {p for p in self.all_items if p.is_active}

    def get_predicates_by_family(self, family: Predicate.Family) -> set[Predicate]:
        """Return all predicates of a given family."""
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_predicates_by_family; repo not initialized')
        with self._lock:
            return {p for p in self.all_items if p.family == family}

    def get_predicates_by_type(self, predicate_type: Predicate.PredicateType) -> set[Predicate]:
        """Return all predicates of a given concrete type."""
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_predicates_by_type; repo not initialized')
        with self._lock:
            return {p for p in self.all_items if p.type == predicate_type}