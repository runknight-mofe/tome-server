from com.runknight.tome.model.device import DeviceType
from com.runknight.tome.db.base_repository import BaseRepository
from com.runknight.tome.db.connection import DBConnector
from com.runknight.tome.model.node import Node

# ---------------------------------------------------------------------------
# NodeDeviceRepo
# Manages unqiue device identities
# Keys: [ID, ORDINAL]
# ---------------------------------------------------------------------------
class NodeRepo(BaseRepository[Node]):
    """Repository for NodeDevice instances."""
 
    __model__ = Node

    KEYS = [Node.ID, Node.NAME]
 
    def __init__(self, db: DBConnector | None = None,db_params: dict | None = None):
        super().__init__(NodeRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_node_devices"
        self.sql[self.ADD]    = "add_many_node_devices"
        self.sql[self.UPDATE] = "update_many_node_devices"
        self.sql[self.REMOVE] = "remove_many_node_devices"

# ---------------------------------------------------------------------------
# DeviceTypeRepo
# Manages hardware platform types
# Keys: [ID, ORDINAL]
# ---------------------------------------------------------------------------
class DeviceTypeRepo(BaseRepository[DeviceType]):
    """Repository for DeviceType hardware platform definitions."""
 
    __model__ = DeviceType

    KEYS = [DeviceType.ORDINAL, DeviceType.NAME]
 
    def __init__(self, db: DBConnector | None = None,db_params: dict | None = None):
        super().__init__(DeviceTypeRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_device_types"
        self.sql[self.ADD]    = "add_many_device_types"
        self.sql[self.UPDATE] = "update_many_device_types"
        self.sql[self.REMOVE] = "remove_many_device_types"