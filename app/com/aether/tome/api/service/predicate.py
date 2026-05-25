from com.aether.tome.api.tome_config import config
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.db.predicate import PredicateRepo

DB_PARAMS = {
    DBConnector.HOST : config.db_host,
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB   : config.db_name,
    DBConnector.PASS : config.db_pass
}

pr = PredicateRepo(db_params=DB_PARAMS)
pr.initialize()


def create_predicate(predicate):
    """Persist a new predicate to the Tome DB.

    Args:
        predicate: A Predicate subclass instance (Point, Sphere, etc.)

    Returns:
        Predicate if successfully created, None otherwise
    """
    return pr.add(predicate)


def retrieve_predicate(id):
    """Retrieve a predicate by its UUID.

    Args:
        id: UUID of the predicate

    Returns:
        Predicate if found, None otherwise
    """
    return pr.get(id)


def enable_predicate(id):
    """Activate a predicate.

    Args:
        id: UUID of the predicate

    Returns:
        bool: True if successfully enabled
    """
    predicate = pr.get(id)
    if not predicate:
        return False
    predicate.is_active = True
    return pr.update(predicate) is not None


def disable_predicate(id):
    """Deactivate a predicate.

    Args:
        id: UUID of the predicate

    Returns:
        bool: True if successfully disabled
    """
    predicate = pr.get(id)
    if not predicate:
        return False
    predicate.is_active = False
    return pr.update(predicate) is not None


def remove_predicate(id):
    """Permanently remove a predicate from the Tome DB.

    Removing a predicate also removes all of its mesh associations via
    the ON DELETE CASCADE constraint on node_mesh_predicates.

    Args:
        id: UUID of the predicate

    Returns:
        Predicate snapshot if successfully removed, None otherwise
    """
    return pr.remove_by_id(id)
