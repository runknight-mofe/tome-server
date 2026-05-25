from com.aether.tome.api.tome_config import config
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.mesh import MeshRepo

DB_PARAMS = {
    DBConnector.HOST : config.db_host, 
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB : config.db_name,
    DBConnector.PASS : config.db_pass
}

mr = MeshRepo(db_params=DB_PARAMS)
mr.initialize()


def retrieve_mesh(id):
    return mr.get(id)

def join_device_to_node_mesh(request):
    """Service request for device joining a node mesh"""
    pass

def remove_device_from_node_mesh(request):
    """Service request for device leaving node mesh"""
    pass

def add_predicate_to_node_mesh(request):
    """Service request for adding a predicate to a node mesh"""
    pass

def remove_predicate_to_node_mesh(request):
    """Service request for removing a predicate from a node mesh"""
    pass