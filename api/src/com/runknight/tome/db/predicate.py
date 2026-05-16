from com.runknight.tome.db.base_repository import BaseRepository
from com.runknight.tome.db.connection import DBConnector
from com.runknight.tome.model.predicate.geometric import Predicate

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
        self.sql[self.GET]    = "SELECT get_all_predicate_metadata()"
        self.sql[self.ADD]    = "SELECT add_many_predicate_metadata(%s::JSONB)"
        self.sql[self.UPDATE] = "SELECT update_many_predicate_metadata(%s::JSONB)"
        self.sql[self.REMOVE] = "SELECT remove_many_predicate_metadata(%s::JSONB)"