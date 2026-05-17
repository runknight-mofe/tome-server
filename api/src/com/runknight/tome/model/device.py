from dataclasses import dataclass
from enum import Enum
from typing import Type

from com.runknight.model.base_model import BaseDataModel

@dataclass(eq = False)
class DeviceType(BaseDataModel):
    """Descriptor for device hardware."""

    class RangingMethod(Enum):
        """Supported ranging methods"""
        TWR         = 0
        """Two-Way Ranging  (each node participates in the exchange)"""
        TDOA        = 1
        """Time Difference of Arrival (infrastructure-side calculation)"""
        TWR_TDOA    = 2
        """Hardware supports both TWR and TDOA modes"""

    class KnownTypes(Enum):
        """Support enumeration for rapidly tagging device types"""
        EMULATED_GENERIC    = 0
        EMULATED_AOA        = 1
        QORVO               = 10
        SEWIO_RTLS          = 100
        POZYX               = 200
        UBISENSE            = 300
        BESPOON             = 400
        APPLE_UI            = 500
        NXP_TRIMENSION      = 600
        CUSTOM              = 700

    ORDINAL             = "ordinal"
    NAME                = "name"
    DESCRIPTION         = "description"
    MANUFACTURER        = "manufacturer"
    RANGING_METHOD      = "ranging_method"
    SUPPORTS_AOA        = "supports_aoa"
    MAX_UPDATE_RATE_HZ  = "max_update_rate_hz"
    TYPICAL_ACCURACY_M  = "typical_accuracy_m"

    EXPECTED_FIELDS = { 
        ORDINAL : int,
        NAME : str,
        DESCRIPTION : str,
        MANUFACTURER: str,
        RANGING_METHOD : int,
        SUPPORTS_AOA : bool,
        MAX_UPDATE_RATE_HZ : int,
        TYPICAL_ACCURACY_M : float 
    }

    OPTIONAL_FIELDS = { }
    FIELD_TYPES = { 
        ORDINAL : int,
        NAME : str,
        DESCRIPTION : str,
        MANUFACTURER: str,
        RANGING_METHOD : RangingMethod,
        SUPPORTS_AOA : bool,
        MAX_UPDATE_RATE_HZ : int,
        TYPICAL_ACCURACY_M : float 
    }

    def __init__(self, params):
        super().__init__(params)
        self._ordinal : int                             = self._data[DeviceType.ORDINAL]
        self._name : str                                = self._data[DeviceType.NAME]
        self._description : str                         = self._data[DeviceType.DESCRIPTION]
        self._manufacturer : str                        = self._data[DeviceType.MANUFACTURER]
        self._ranging_method : DeviceType.RangingMethod = self._data[DeviceType.RANGING_METHOD]
        self._supports_aoa : bool                       = self._data[DeviceType.SUPPORTS_AOA]
        self._max_update_rate_hz : int                = self._data[DeviceType.MAX_UPDATE_RATE_HZ]
        self._typical_accuracy_m : float                = self._data[DeviceType.TYPICAL_ACCURACY_M]


    @property
    def ordinal(self):
        """Numerical identifier"""
        return self._ordinal

    @ordinal.setter
    def ordinal(self, value : int):
        self._ordinal = value
        self.set_field_value(DeviceType.ORDINAL, value)

    @property
    def name(self):
        """Human readable name"""
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value
        self.set_field_value(DeviceType.NAME, value)

    @property
    def description(self):
        """Human readable description"""
        return self._description

    @description.setter
    def description(self, value : str):
        self._description = value
        self.set_field_value(DeviceType.DESCRIPTION, value)

    @property
    def manufacturer(self):
        """Device manufacturer"""
        return self._manufacturer

    @manufacturer.setter
    def manufacturer(self, value : str):
        self._manufacturer = value
        self.set_field_value(DeviceType.MANUFACTURER, value)

    @property
    def ranging_method(self):
        """Supported ranging method"""
        return self._ranging_method

    @ranging_method.setter
    def ranging_method(self, value : RangingMethod):
        self._ranging_method = value
        self.set_field_value(DeviceType.RANGING_METHOD, value)

    @property
    def supports_aoa(self):
        """Does the device support Angle-of-Attack?"""
        return self._supports_aoa

    @supports_aoa.setter
    def supports_aoa(self, value : bool):
        self._supports_aoa = value
        self.set_field_value(DeviceType.SUPPORTS_AOA, value)

    @property
    def max_update_rate_hz(self):
        """Maximum range data transmission rate"""
        return self._max_update_rate_hz

    @max_update_rate_hz.setter
    def max_update_rate_hz(self, value : int):
        self._max_update_rate_hz = value
        self.set_field_value(DeviceType.MAX_UPDATE_RATE_HZ, value)

    @property
    def typical_accuracy_m(self):
        """Average error for device ranging capability measurements (in meters)"""
        return self._typical_accuracy_m

    @typical_accuracy_m.setter
    def typical_accuracy_m(self, value : float):
        self._typical_accuracy_m = value
        self.set_field_value(DeviceType.TYPICAL_ACCURACY_M, value)

    def __hash__(self):
        return hash(self.ordinal)

    def __str__(self):
        return self.name

    def __repr__(self) -> str:
        return f'{self.ordinal}:{self.name}'

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return DeviceType.EXPECTED_FIELDS

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return DeviceType.OPTIONAL_FIELDS

    @staticmethod
    def get_field_types():
        return  DeviceType.FIELD_TYPES