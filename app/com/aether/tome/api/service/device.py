
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.api.tome_config import config
from com.aether.tome.db.device import DeviceRepo

DB_PARAMS = {
    DBConnector.HOST : config.db_host, 
    DBConnector.PORT : config.db_port,
    DBConnector.USER : config.db_user,
    DBConnector.DB : config.db_name,
    DBConnector.PASS : config.db_pass
}

dm = DeviceRepo(db_params=DB_PARAMS)
dm.initialize()

def retrieve_device(id):
    """Retrieve a managed device handle by its id"""
    return dm.get(id)

def enable_device(id):
    """Enables an existing device managed in the Tome repo"""
    return dm.enable_device(id)

def disable_device(id):
    """Disable n existing device managed in the Tome repo"""
    return dm.disable_device(id)

def register_device(device):
    """Handles registering a unique device to tome"""
    return dm.add(device)

def unregister_device(id):
    """Handles un-registering a unique device from tome"""
    return dm.remove_by_id(id)