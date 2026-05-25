from com.aether.tome.model.device import Device, DeviceType
from com.aether.tome.db.base_repository import BaseRepository
from com.aether.tome.db.connection import DBConnector
from com.aether.tome.model.node import Node

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

# ---------------------------------------------------------------------------
# DeviceRepo
# Manages hardware platform types
# Keys: [ID, NAME]
# ---------------------------------------------------------------------------
class DeviceRepo(BaseRepository[Device]):
    """Repository for DeviceType hardware platform definitions."""
 
    __model__ = Device

    KEYS = [Device.ID, Device.NAME]
 
    def __init__(self, db: DBConnector | None = None,db_params: dict | None = None):
        super().__init__(DeviceRepo.KEYS, db, db_params)
        self.sql[self.GET]    = "get_all_devices"
        self.sql[self.ADD]    = "add_many_devices"
        self.sql[self.UPDATE] = "update_many_devices"
        self.sql[self.REMOVE] = "remove_many_devices"

    # -----------------------------------------------------------------------
    # Registration: Get or create (idempotent)
    # -----------------------------------------------------------------------
    def get_or_create(self, name: str, device_type_ordinal: int,
                     description: str | None = None,
                     is_emulated: bool = False) -> Device | None:
        """
        Idempotent device registration.
        
        If a device with this name exists, return it.
        Otherwise, atomically create a new device.
        
        This is the **primary workflow** for device management:
        1. Check if device already registered (by name)
        2. If yes, reuse it across meshes
        3. If no, register it once
        
        Args:
            name: Device name (globally unique identifier)
            device_type_ordinal: Hardware type ordinal (FK to device_types)
            description: Optional notes (immutable after creation)
            is_emulated: True if device is software-simulated
        
        Returns:
            Device (existing or newly created), or None on error
        
        Example:
            device = device_repo.get_or_create(
                name="uwb_tag_001",
                device_type_ordinal=14,  # DW3000
                description="Portable UWB tag for asset tracking",
                is_emulated=False
            )
            # First call: creates device; returns it
            # Second call with same name: returns existing device
            # Third call with same name: returns existing device
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_or_create; repo not initialized')
 
        # Check if device with this name already exists
        existing = self.get(name, field=Device.NAME)
        if existing:
            self.logger.debug(f"Device '{name}' already registered; reusing {existing.id}")
            return existing
 
        # Create new device
        self.logger.info(f"Registering new device: {name} (type={device_type_ordinal})")
        device = Device({
            Device.ID: None,  # DB generates UUID via gen_random_uuid()
            Device.NAME: name,
            Device.DESCRIPTION: description or "",
            Device.TYPE: device_type_ordinal,
            Device.IS_ACTIVE : True,
            Device.IS_EMULATED: is_emulated,
            Device.CREATED_AT: None  # DB generates CURRENT_TIMESTAMP
        })
 
        result = self.add(device)
        if result:
            self.logger.info(f"Device registered: {result.name} ({result.id})")
        else:
            self.logger.error(f"Failed to register device {device.name}; check underlying DB connection")
        return result
 
    # -----------------------------------------------------------------------
    # Filtering: By device type
    # -----------------------------------------------------------------------
    def get_devices_by_type(self, device_type_ordinal: int) -> set[Device]:
        """
        Get all registered devices of a specific hardware type.
        
        Useful for querying "all DW3000s" or "all Sewio anchors".
        
        Args:
            device_type_ordinal: DeviceType ordinal (e.g., 14 for DW3000)
        
        Returns:
            Set of Device objects matching the type
        
        Example:
            dw3000_devices = device_repo.get_devices_by_type(14)
            for device in dw3000_devices:
                print(f"{device.name}: {device.device_type_ordinal}")
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_devices_by_type; repo not initialized')
 
        with self._lock:
            return {d for d in self.all_items
                   if d.type_ordinal == device_type_ordinal}
 
    # -----------------------------------------------------------------------
    # Filtering: Emulated vs. physical
    # -----------------------------------------------------------------------
    def get_emulated_devices(self) -> set[Device]:
        """
        Get all software-simulated (emulated) devices.
        
        Useful for test/development environments or UI filtering.
        
        Returns:
            Set of emulated Device objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_emulated_devices; repo not initialized')
 
        with self._lock:
            return {d for d in self.all_items if d.is_emulated}
 
    def get_physical_devices(self) -> set[Device]:
        """
        Get all physical (non-emulated) devices.
        
        Useful for filtering to "real hardware" in operational systems.
        
        Returns:
            Set of physical Device objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_physical_devices; repo not initialized')
 
        with self._lock:
            return {d for d in self.all_items if not d.is_emulated}
 
    # -----------------------------------------------------------------------
    # Enabled / Disabled
    # -----------------------------------------------------------------------
    def enable_device(self, id):
        """Raises active flag on a managed device
        
        Useful for re-enabling previously disabled devices.
        
        Returns:
            True if device was found and enabled, False otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.enable_device; repo not initialized')
        existing = self.get(id)
        if existing:
            existing.is_active = True
            return super().update(existing) is not None
        return False

    def disable_device(self, id):
        """Lowers active flag on a managed device
        
        Useful for preventing devices from operating while retaining them in DB.
        
        Returns:
            True if device was found and disabled, False otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.disable_device; repo not initialized')
        existing = self.get(id)
        if existing:
            existing.is_active = False
            return super().update(existing) is not None
        return False

    def get_active_devices(self) -> set[Device]:
        """
        Get all active devices.

        Useful for filtering out disabled devices.

        Returns:
            Set of active Device objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_active_devices; repo not initialized')

        with self._lock:
            return {d for d in self.all_items if d.is_active}

    def get_inactive_devices(self) -> set[Device]:
        """
        Get all inactive devices.

        Useful for looking up disabled devices

        Returns:
            Set of inactive Device objects
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get_inactive_devices; repo not initialized')

        with self._lock:
            return {d for d in self.all_items if not d.is_active}

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------
    def device_count(self) -> int:
        """
        Fast count of registered devices (no object construction).
        
        Returns:
            Total count of devices in registry
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.device_count; repo not initialized')
 
        with self._lock:
            return len(self.all_items)
 
    def device_count_by_type(self, device_type_ordinal: int) -> int:
        """
        Count devices of a specific type (no object construction).
        
        Args:
            device_type_ordinal: Hardware type to count
        
        Returns:
            Count of devices with that type
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.device_count_by_type; repo not initialized')
 
        with self._lock:
            return sum(1 for d in self.all_items
                      if d.type_ordinal == device_type_ordinal)

    # -----------------------------------------------------------------------
    # Immutability enforcement: DELETE is rarely needed, UPDATE never
    # -----------------------------------------------------------------------
    def remove(self, arg: Device) -> Device | None:
        """
        Remove a device from the registry.

        ⚠️  USE WITH CAUTION. Devices are meant to be immutable and auditable.
        Consider marking devices inactive rather than deleting.

        Removal cascades to node_mesh_memberships (FK ON DELETE CASCADE),
        so all mesh associations are automatically cleaned up.

        Args:
            arg: Device to remove

        Returns:
            Device if successfully removed, None otherwise
        """
        self.logger.warning(f"Removing device {arg.name} from registry; "
                           f"all mesh memberships will be cleaned up")
        return super().remove(arg)
 
    def update(self, arg: Device):
        """
        This method is not supported for Device.

        Devices are immutable after registration. If you need to change
        device properties, create a new device and migrate mesh memberships.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError(
            "Device properties are immutable after registration. "
            "Create a new device if properties need to change."
        )
 
 