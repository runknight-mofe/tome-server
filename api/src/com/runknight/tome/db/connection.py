import logging
from typing import Any

import psycopg2
from psycopg2 import DatabaseError
from psycopg2.extensions import connection, cursor
from psycopg2.pool import ThreadedConnectionPool

from com.runknight.common.validation import validateData

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))

class DBConnector:

    HOST = "HOST"
    PORT = "PORT"
    DB = "DB"
    USER = "USER"
    PASS = "PASS"

    EXPECTED_PARAMS = { HOST : str, PORT : int, DB : str, USER : str }
    """Params required for DB Connector at init"""

    OPTIONAL_PARAMS = { PASS : str }
    """Non required params for DB Connector at init"""

    def __init__(self, params, max_pool_size = 1):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(log_handler)

        self.conn: connection | None = None

        validateData(data=params, expected=DBConnector.EXPECTED_PARAMS, optional=DBConnector.OPTIONAL_PARAMS)

        self.host = params[DBConnector.HOST]
        self.port = params[DBConnector.PORT]
        self.db = params[DBConnector.DB]
        self.user = params[DBConnector.USER]
        self.password = params[DBConnector.PASS] if DBConnector.PASS in params else None

        pool = ThreadedConnectionPool(
            1, max_pool_size, 
            user = self.user,
            password = self.password,
            host = self.host,
            port = self.port,
            database = self.db)

    def is_connected(self):
        return not self.conn is None and not self.conn.closed != 0

    def connect(self):
        """Create the connection

        Retrieves the singleton instance for the DB connection

        Returns:
            connection: The connection to the wordgame backend db
        """
        connected = self.is_connected()
        if not connected:
            # Connection does not exist or is closed, so create another
            try:
                self.conn =  psycopg2.connect(
                    host = self.host,
                    port = self.port,
                    user = self.user,
                    password = self.password,
                    dbname = self.db)
            except DatabaseError as e:
                self.logger.exception(e)
                raise e
            finally:
                connected = self.is_connected()

        return connected

    def getCursor(self):
        """Retrieve the connection cursor

        Creates and returns a cursor instance for the db connection

        Returns:
            cursor: The cursor instance for the db connection
        """
        try:
            if self.connect() and self.conn:
                return self.conn.cursor()
            raise DatabaseError("Could not generate cursor do to failure to establish db connection")
        except DatabaseError as e:
            self.logger.exception(e)
            raise e

    def execute(self, sql: str, args = None, fetchMany: bool = False):# -> tuple[Any, ...] | None | list[tuple[Any, ...]]:
        """Execute a SQL statement

        Args:
            sql (str): SQL statement string
            args (tuple[Any, ...], optional): Arguments to inject into the SQL statement. Defaults to None.
            fetchMany (bool, optional): Indicates whether the statement should return many objects. Defaults to False.

        Raises:
            DatabaseError: If the execution of the SQL statement throws an error

        Returns:
            tuple[Any, ...] | None: Tuple of results from the executed statement
        """

        results: list[tuple[Any,...]] = []
        cur: cursor | None = None

        try:
            cur = self.getCursor()
            if isinstance(cur, cursor):
                cur.execute(sql, args)
                if cur.pgresult_ptr is not None:
                    if False == fetchMany:
                        # Fetch One
                        res = cur.fetchone()
                        if not res is None and res:
                            if isinstance(res, list):
                                # One matching result found
                                if not res[0] is None and res[0]:
                                    results.append(res[0])
                            elif isinstance(res, tuple):
                                if not res[0] is None and res[0]:
                                    results.append(res[0])
                            else:
                                results.append(res)
                    else:
                        # Fetch Many
                        res = cur.fetchall()
                        if not res is None and res:
                            if isinstance(res, list):
                                # Result was a list of multiple objects
                                results.extend([item[0] for item in res if item[0]])
                            else:
                                # Result was a single object
                                results.append(res[0])
        except DatabaseError as e:
            self.logger.error(e)
            raise e
        finally:
                if cur : cur.close()
        return results

    def commit(self) -> bool:
        """Commits any active statements
        
        Commits any executed statements for the connection, if it is open

        Returns:
            True if there is an open connection, False otherwise
        """

        committed: bool = False

        if self.conn and psycopg2.extensions.STATUS_IN_TRANSACTION == self.conn.status:
            # Connection is instantiated and has uncommitted transactions
            self.conn.commit()
            committed = True

        return committed