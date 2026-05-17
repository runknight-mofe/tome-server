from com.runknight.tome.db.base_repository import BaseRepository
from com.runknight.tome.db.connection import DBConnector
from com.runknight.tome.model.predicate.base import Predicate

# ---------------------------------------------------------------------------
# PredicateRepo
# Keys: [ID]
# ---------------------------------------------------------------------------
class PredicateRepo(BaseRepository[Predicate]):
    """Repository for all predicates."""
 
    __model__ = Predicate

    KEYS = [Predicate.ID]
 
    def __init__(self, db: DBConnector | None = None,db_params: dict | None = None):
        super().__init__(PredicateRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_predicates"
        self.sql[self.ADD]    = "add_many_predicates"
        self.sql[self.UPDATE] = "update_many_predicates"
        self.sql[self.REMOVE] = "remove_many_predicates"