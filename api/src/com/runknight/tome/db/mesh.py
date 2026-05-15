from com.runknight.tome.db.connection import DBConnector, cursor
from com.runknight.tome.model.mesh import NodeMesh
from .base_repository import BaseRepository


class MeshRepo(BaseRepository[NodeMesh]):
    """Data repository managing instances of NodeMesh """
    
    __model__ = NodeMesh

    SELECT_ALL = "SELECT * FROM node_meshes"

    KEYS = [NodeMesh.ID, NodeMesh.NAME]
    
    def __init__(self, db: DBConnector | None = None, db_params: dict | None = None):
        super().__init__(MeshRepo.KEYS, db, db_params)

    def sql_get_all(self) -> str:
        """get all mesh intances sql string"""
        return MeshRepo.SELECT_ALL

    def sql_add_func(self, placeholder: str) -> str:
        """SQL for BaseRepository.add_many()"""
        return "SELECT add_many_node_meshes(%s::JSONB)"

    def sql_update_func(self, placeholder: str) -> str:
        """SQL for BaseRepository.update_many()"""
        return "SELECT update_many_node_meshes(%s::JSONB)"

    def sql_remove_func(self, placeholder: str) -> str:
        """SQL for BaseRepository.remove_many()"""
        return "SELECT remove_many_node_meshes(%s::JSONB)"