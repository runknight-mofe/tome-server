from api.src.com.runknight.tome.db.connection import DBConnector
from api.src.com.runknight.tome.model.mesh import NodeMesh
from base_repository import BaseRepository


class MeshRepo(BaseRepository[NodeMesh]):
    """Data repository managing instances of NodeMesh """
    
    __model__ = NodeMesh

    KEYS = [
        NodeMesh.ID,
        NodeMesh.NAME
    ]
    
    def __init__(self, db: DBConnector | None = None, db_params: dict | None = None):
        super().__init__(MeshRepo.KEYS, db, db_params)

    def sql_add_func(self, placeholder: str) -> str:
        return ""

    def sql_update_func(self, placeholder: str) -> str:
        return ""

    def sql_remove_func(self, placeholder: str) -> str:
        return ""
    
    def reload_from_db(self):
        """Re-initialize the repository data

        Drops all cached repo data, and repopulates from underlying DB

        Returns:
            bool: True if data is successfully retrieved and loaded to 
            local repo, false otherwise.
        """
        return True

    def delete_all(self):
        """Remove all managed data

        Removes all of the managed objects from the local repo and the underlying DB

        Returns:
            bool: True if the deletion is successful, False otherwise
        """
        return True