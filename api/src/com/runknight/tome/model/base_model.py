from abc import ABC
from ctypes import Union
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from typing import Any, Type, get_args, get_origin
from uuid import UUID
from packaging.version import Version

from msgspec import ValidationError

from data.validation import validateData

class BaseDataModel(ABC):

    def __init__(self, params : dict | None = None) -> None:
        self._data = params if params else {}

        # All strings are rendered uppercase
        for key, value in self._data.items():
            if isinstance(value, str):
                self._data[key] = value.upper()

    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """Generic getter that retrieves value from _data dict.
        
        Args:
            field_name: The key in _data to retrieve
            default: Default value if field_name not found
            
        Returns:
            The value from _data or default
        """
        return self._data.get(field_name, default)

    def set_field_value(self, field_name: str, value: Any) -> None:
        """Generic setter that updates both _data dict and instance attribute.
        
        Args:
            field_name: The key in _data to update
            value: The value to set
        """
        # Update the _data dictionary
        self._data[field_name] = value
        
        # Also update the instance attribute if it exists
        # Convert field_name to attribute name (you may need to customize this mapping)
        private_attr_name = f"_{self._get_attribute_name(field_name)}"
        if hasattr(self, private_attr_name):
            setattr(self, private_attr_name, value)

    def _get_attribute_name(self, field_name: str) -> str:
        """Convert field name to attribute name.
        Override this in child classes for custom mapping.
        
        Args:
            field_name: The field name from _data
            
        Returns:
            The corresponding attribute name
        """
        return field_name

    def update_data_from_attributes(self) -> None:
        """Update _data dict from current instance attribute values."""
        # Get the field types to know which attributes to sync
        field_types = self.get_field_types()
        
        for field_name in field_types.keys():
            attr_name = self._get_attribute_name(field_name)
            if hasattr(self, attr_name):
                attr_value = getattr(self, attr_name)
                # Handle the special case where "name" attribute maps to "value" field
                if field_name == "value" and hasattr(self, "name"):
                    self._data[field_name] = attr_value
                else:
                    self._data[field_name] = attr_value

    def sync_attribute_to_data(self, attr_name: str, field_name: str  | None = None) -> None:
        """Sync a specific attribute value back to _data.
        
        Args:
            attr_name: The attribute name to sync
            field_name: The field name in _data (defaults to attr_name)
        """
        if field_name is None:
            field_name = attr_name
            
        if hasattr(self, attr_name):
            self._data[field_name] = getattr(self, attr_name)

    @staticmethod
    def get_required_fields() -> dict[str, Type]:
        return {}

    @staticmethod
    def get_optional_fields() -> dict[str, Type]:
        return {}

    @staticmethod
    def get_field_types():
        return {}

    def to_dict(self):
        data = {}

        for key, value in self._data.items():
            data[key] = DataModelServices.serialize_value(value)

        return data

    @classmethod
    def from_dict(cls, data):
        expected_fields = cls.get_required_fields()
        optional_fields = cls.get_optional_fields()
        validateData(
            data = data,
            expected = expected_fields,
            optional = optional_fields
        )

        attrs = {}
        field_types = cls.get_field_types()
        for field_name in expected_fields.keys():
            if field_name in data:
                attrs[field_name] = DataModelServices.deserialize_value(
                    field_name=field_name,
                    field_type=field_types[field_name],
                    value=data[field_name]
                )

        for field_name in optional_fields.keys():
            if field_name in data:
                attrs[field_name] = DataModelServices.deserialize_value(
                    field_name=field_name,
                    field_type=field_types[field_name],
                    value=data[field_name]
                )

        return cls(attrs)

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, data):
        obj = json.loads(data)
        return cls.from_dict(obj)

    def __eq__(self, other) -> bool:
        if isinstance(other, type(self)):
            # Make sure both objects have up-to-date _data
            self.update_data_from_attributes()
            other.update_data_from_attributes()
            return self._data == other._data
        return False

    def __hash__(self) -> int:
        return hash(self._data)

class DataModelServices:
    
    @staticmethod
    def serialize_value(value: Any) -> Any:
        """
        Serialize a value for JSON/dict output, handling all supported types uniformly.

        Args:
            value: The value to serialize
            target_type: Optional type hint for better serialization

        Returns:
            Serialized value suitable for JSON
        """
        if value is None:
            return None

        # Handle BaseDataModel instances (composite objects)
        if isinstance(value, BaseDataModel):
            return value.to_dict()

        # Handle lists/arrays
        elif isinstance(value, (list, tuple)):
            return [DataModelServices.serialize_value(item) for item in value]

        # Handle dictionaries
        elif isinstance(value, dict):
            return {k: DataModelServices.serialize_value(v) for k, v in value.items()}

        # Handle datetime objects
        elif isinstance(value, datetime):
            return value.isoformat()

        # Handle date objects
        elif isinstance(value, date):
            return value.isoformat()

        # Handle Decimal objects
        elif isinstance(value, Decimal):
            return str(value)  # Use string to preserve precision

        # Handle Enum objects
        elif isinstance(value, Enum):
            return value.name

        elif isinstance(value, UUID):
            return str(value)

        elif isinstance(value, Version):
            return str(value)

        # Handle sets (convert to list)
        elif isinstance(value, set):
            return [DataModelServices.serialize_value(item) for item in value]

        # Primitive types (int, str, bool, float) pass through
        else:
            return value

    @staticmethod
    def deserialize_value(value: Any, field_name: str, field_type: Any) -> Any:
        """
        Deserialize a value from JSON/dict input, handling all supported types uniformly.

        Args:
            value: The value to deserialize
            field_name: The name of the field to deserialize
            field_type: data type of the deserialized field

        Returns:
            Deserialized value of the correct type

        Raises:
            ValidationError: If deserialization fails
        """
        if value is None:
            return None

        field_name = field_name or "unknown_field"

        try:
            # Handle generic types (List, Dict, Optional, etc.)
            origin_type = get_origin(field_type)
            type_args = get_args(field_type)

            # Handle Optional[T] (which is Union[T, None])
            if origin_type is Union:
                # Find the non-None type
                non_none_types = [t for t in type_args if t is not type(None)]
                if len(non_none_types) == 1:
                    return DataModelServices.deserialize_value(value, non_none_types[0], field_name)
                else:
                    # Multiple non-None types - use the first one (basic union handling)
                    return DataModelServices.deserialize_value(value, non_none_types[0], field_name)

            # Handle List[T]
            elif origin_type is list or field_type is list:
                if not isinstance(value, (list, tuple)):
                    raise ValidationError(field_name, f"Expected list, got {type(value).__name__}")

                if type_args:
                    item_type = type_args[0]
                    return [DataModelServices.deserialize_value(item, item_type, f"{field_name}[{i}]") 
                           for i, item in enumerate(value)]
                else:
                    return list(value)

            # Handle Dict[K, V]
            elif origin_type is dict or field_type is dict:
                if not isinstance(value, dict):
                    raise ValidationError(field_name, f"Expected dict, got {type(value).__name__}")

                if type_args and len(type_args) == 2:
                    key_type, value_type = type_args
                    return {
                        DataModelServices.deserialize_value(k, key_type, f"{field_name}.key"): 
                        DataModelServices.deserialize_value(v, value_type, f"{field_name}[{k}]")
                        for k, v in value.items()
                    }
                else:
                    return dict(value)

            # Handle BaseDataModel subclasses (composite objects)
            elif (isinstance(field_type, type) and 
                  issubclass(field_type, BaseDataModel)):
                if isinstance(value, dict):
                    return field_type.from_dict(value)
                elif isinstance(value, field_type):
                    return value
                else:
                    raise ValidationError(field_name, 
                                        f"Cannot convert {type(value).__name__} to {field_type.__name__}")

            # Handle datetime
            elif field_type is datetime:
                if isinstance(value, str):
                    # Try multiple datetime formats
                    for fmt in [
                        "%Y-%m-%dT%H:%M:%S.%fZ",      # ISO format with microseconds and Z
                        "%Y-%m-%dT%H:%M:%S.%f",       # ISO format with microseconds
                        "%Y-%m-%dT%H:%M:%SZ",         # ISO format with Z
                        "%Y-%m-%dT%H:%M:%S",          # ISO format basic
                        "%Y-%m-%d %H:%M:%S",          # SQL datetime format
                    ]:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue

                    # Try fromisoformat as fallback
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValidationError(field_name, f"Invalid datetime format: {value}")
                elif isinstance(value, datetime):
                    return value
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to datetime")

            # Handle date
            elif field_type is date:
                if isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value).date()
                    except ValueError:
                        try:
                            return datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            raise ValidationError(field_name, f"Invalid date format: {value}")
                elif isinstance(value, date):
                    return value
                elif isinstance(value, datetime):
                    return value.date()
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to date")

            # Handle Decimal
            elif field_type is Decimal:
                if isinstance(value, (str, int, float, Decimal)):
                    return Decimal(str(value))
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to Decimal")

            # Handle Enum subclasses
            elif (isinstance(field_type, type) and 
                  issubclass(field_type, Enum)):
                if isinstance(value, field_type):
                    return value
                else:
                    # Try to create enum from value
                    try:
                        if (isinstance(value, int)):
                            # Assume Enum ordinal value provided
                            return field_type(value)
                        # Assume it is the string name of the Enum instance
                        return field_type[value]
                    except ValueError:
                        valid_values = [e.value for e in field_type]
                        raise ValidationError(field_name, 
                                            f"Invalid enum value '{value}'. Valid values: {valid_values}")

            # Handle UUID
            elif field_type is UUID:
                if isinstance(value, str):
                    return UUID(value)
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to UUID")

            elif field_type is Version:
                if isinstance(value, str):
                    return Version(value)
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to Version")

            # Handle primitive types with conversion
            elif field_type in (int, str, bool, float):
                if isinstance(value, field_type):
                    return value
                else:
                    try:
                        return field_type(value)
                    except (ValueError, TypeError):
                        raise ValidationError(field_name, 
                                            f"Cannot convert {type(value).__name__} to {field_type.__name__}")

            # Handle set types
            elif field_type is set or origin_type is set:
                if isinstance(value, (list, tuple, set)):
                    if type_args:
                        item_type = type_args[0]
                        return {DataModelServices.deserialize_value(item, item_type, f"{field_name}.item") 
                               for item in value}
                    else:
                        return set(value)
                else:
                    raise ValidationError(field_name, f"Cannot convert {type(value).__name__} to set")

            # Default case - return as-is
            else:
                return value

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(field_name, f"Deserialization error: {str(e)}")