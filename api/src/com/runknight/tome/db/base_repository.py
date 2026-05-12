from abc import ABC, abstractmethod
import logging
from typing import Any, Generic,  TypeVar

from base_model import BaseDataModel

from .connection import DBConnector
from psycopg2.extras import Json

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))

T = TypeVar('T', bound=BaseDataModel)

class BaseRepository(ABC, Generic[T]):
    """Base service layer for data object managers"""

    __model__ : type[T]

    def __init__(self, keys: list[str], db: DBConnector | None = None, db_params : dict | None = None):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(log_handler)

        if db:
            self.connector = db
            """Connection to the underlying persistent database"""
        elif db_params:
            self.connector = DBConnector(db_params)
        else:
            raise TypeError("Requires a DBConnection; neither an instance nor params for constructing one were supplied")

        self.keys = keys
        """list of indices by which managed objects are mapped"""

        self.indices: dict[str, dict[Any, T]] = { key : {} for key in keys }
        """Mapping of all managed data objects"""

        self.initialized = False
        """Initialization flag for data dict; data dict is lazy loaded"""

    @abstractmethod
    def sql_add_func(self, placeholder: str) -> str:
        raise NotImplementedError(f'type{self} does not implement required "sql_add_func" method.')

    @abstractmethod
    def sql_update_func(self, placeholder: str) -> str:
        raise NotImplementedError(f'type{self} does not implement required "sql_update_func" method.')

    @abstractmethod
    def sql_remove_func(self, placeholder: str) -> str:
        raise NotImplementedError(f'type{self} does not implement required "sql_remove_func" method.')

    def initialize(self) -> bool:
        """Prime the repository

        Prime the repo, establishing backend DB connection and fetching data.

        Returns:
            True if the repo is initialized, False otherwise
        """
        # Guards against multiple initializations
        if False == self.initialized:

            self.logger.debug(f"Initializing ${type(self)}...")

            # Repository is initialize after all data is cached
            self.initialized = self.reload_from_db()

            self.logger.debug(f"Initialized ${type(self)}...")

        return self.initialized

    @abstractmethod
    def reload_from_db(self) -> bool:
        """Re-initialize the repository data

        Drops all cached repo data, and repopulates from underlying DB

        Returns:
            bool: True if data is successfully retrieved and loaded to 
            local repo, false otherwise.
        """
        raise NotImplementedError(f'{type(self)} is missing required "reload_from_db(self)" function implementation.')

    @abstractmethod
    def delete_all(self) -> bool:
        """Remove all managed data

        Removes all of the managed objects from the local repo and the underlying DB

        Returns:
            bool: True if the deletion is successful, False otherwise
        """
        raise NotImplementedError(f'{type(self)} is missing required "delete_all(self)" function implementation.')

    def get(self, arg: Any, field: str):
        """Retrieve managed object
        
        Retrieve managed object with matching field key of value arg
        
        Args:
            field(_str_): Field name
            arg(_Any_): Value for field
        
        Returns:
            T | None: Managed object if found, None otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.get; repo not initialized; check underlying DB connection')

        return self.indices[field][arg]

    def add(self, arg: T):
        """Add managed object

        Add managed object of type T

        Args:
            arg(_T_): Managed data type

        Returns:
            T | None: Managed object if successfully added, None otherwise
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.add; repo not initialized; check underlying DB connection')

        added = self.add_many({arg})
        return added[0] if added else None

    def add_many(self, objs: set[T]):
        """Add multiple managed objects

        Add managed set of objects of type T

        Args:
            arg(_set[T]_): Set of managed data type
        
        Returns:
            list[T]: list of managed objects successfully added
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.add_many; repo not initialized; check underlying DB connection')

        added_items = list[T]()

        # Filter out objects that already exist in local repo
        index = self.indices[self.keys[0]]
        existing = { obj for obj in objs if obj.get_field_value(self.keys[0]) in index }

        # Determine which objects are not in local repo
        to_add = objs.difference(existing)

        if to_add:
            # Serialize the missing objects to JSON and invoke the SQL insert
            # function
            serialized =  [Json(obj.to_dict()) for obj in to_add]

            # Add the objects to the underlying DB
            placeholder = ', '.join(['%s'] * len(serialized))
            sql = self.sql_add_func(placeholder)
            self.logger.debug(f"{type(self)}::add func SQL: {sql}")
            results = self.connector.execute(sql, serialized, fetchMany = True)

            # If objects are successfully added to DB
            if results and self.connector.commit():
                # Iterate over each added object
                for result in results:
                    # Add it to the local repo and return dict
                    added: T = self.__model__.from_dict(result)
                    for key in self.keys:
                        self.indices[key][added.get_field_value(key)] = added
                        added_items.append(added)

        return added_items

    def update(self, arg):
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.upddate; repo not initialized; check underlying DB connection')

        updated = self.update_many({arg})
        return updated[0] if updated else None

    def update_many(self, objs: set[T]):
        """Update multiple managed objects

        Update managed set of objects of type T

        Args:
            arg(_set[T]_): Set of managed objects to update

        Returns:
            list[T]: list of managed objects successfully updated
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.update_many; repo not initialized; check underlying DB connection')

        updated = list[T]()


        # Detect any unmanaged objects; uses primary key for filtering
        missing = {obj for obj in objs if obj.get_field_value(self.keys[0]) not in self.indices[self.keys[0]]}
        if missing:
            self.logger.warning(f"Skip updating {len(missing)} {self.__model__.__name__} objects; field {self.keys[0]} value did not match record in repo")

        # Determine which objects are managed in local repo and can be updated
        to_update = objs.difference(missing)
        if to_update:
            # Update the objects in the underlying DB

            serialized= [Json(user.to_dict()) for user in to_update]

            placeholder = ', '.join(['%s'] * len(serialized))
            sql = self.sql_update_func(placeholder)
            results = self.connector.execute(sql, serialized, fetchMany = True)

            # If users are successfully updated in DB
            if results and self.connector.commit():
                # Iterate over each added word, updating local repo entries
                for result in results:
                    obj: T = self.__model__.from_dict(result)
                    for key in self.keys:
                        self.indices[key][obj.get_field_value(key)] = obj
                        updated.append(obj)

        return updated

    def remove(self, arg):
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.remove; repo not initialized; check underlying DB connection')

        removed = self.remove_many({arg})
        return removed[0] if removed else None

    def remove_many(self, objs: set[T]):
        """Remove multiple managed objects

        Remove managed set of objects of type T

        Args:
            arg(_set[T]_): Set of managed objects to remove

        Returns:
            list[T]: list of managed objects successfully removed
        """
        if not (self.initialized or self.initialize()):
            raise RuntimeError(f'Failed {type(self)}.add_many; repo not initialized; check underlying DB connection')

        removed = list[T]()

        # Determine which objects are not in local repo
        to_remove = objs

        to_skip = set[T]()

        for obj in objs:
            # Verify field data for supplied objects matches those in managed repo; skip removal of any that do not
            for key in self.keys:
                if not obj.get_field_value(key) in self.indices[key]:
                    to_skip.add(obj)
                    to_remove.remove(obj)
                    self.logger.warning(f'Skip removing {self.__model__.__name__}; value for supplied field {key} does not match that of managed record')
                    break

        if to_skip:
            self.logger.info(f"Skipping {len(to_skip)} of {len(objs)} {self.__model__.__name__} for removal; objects not found in local repo.")

        # If input set contained managed objects
        if to_remove:
            # Convert the Objects to JSON for deletion from DB
            to_remove_serialized = ([ Json(user.to_dict()) for user in to_remove ])

            # Remove Objects.  Removed set is returned
            placeholder = ', '.join(['%s'] * len(to_remove_serialized))
            sql = self.sql_remove_func(placeholder)
            self.logger.debug(f"{type(self)}::remove func SQL: {sql}")
            results = self.connector.execute(
                sql,
                to_remove_serialized,
                fetchMany = True
            )

            # If transaction completed successfully
            if results and self.connector.commit():

                # Iterate over removed objects
                for result in results:
                    # Pop each from local repo and add to return dict
                    obj: T = self.__model__.from_dict(result)
                    for key in self.keys:
                        self.indices[key].pop(obj.get_field_value(key))
                        removed.append(obj)

                    # TODO:  Add event emits for DB changes
                    # Notify listeners of the removed user
                    # event_bus.emit(EventType.OBJ_DELETED, obj)

        return removed