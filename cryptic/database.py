import os

import sqlalchemy

# noinspection PyProtectedMember
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from cryptic.errors import UnknownDBMSTypeError
from cryptic.config import Config


class DatabaseWrapper:
    def __init__(self, config: Config):
        self._config = config
        self.engine = None
        self._SessionFactory = None
        self.Session = None
        self.Base = None

        self._setup_database()

    @staticmethod
    def __setup_sqlite(filename: str, storage_location: str = "data/") -> Engine:
        if not os.path.exists(storage_location):
            os.makedirs(storage_location)

        return sqlalchemy.create_engine("sqlite:///" + os.path.join(storage_location, filename))

    @staticmethod
    def __setup_mysql(username: str, password: str, hostname: str, port: int, database: str) -> Engine:
        assert 0 < port <= 65535, "Invalid port number"
        return sqlalchemy.create_engine(
            f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}", pool_pre_ping=True
        )

    def _setup_database(self):
        if self._config["DBMS"] == "sqlite":
            self.engine = self.__setup_sqlite(self._config["SQLITE_FILE"], self._config["DATA_LOCATION"])
        elif self._config["DBMS"] == "mysql":
            port_str = self._config["MYSQL_PORT"]
            assert port_str.isdecimal(), "Invalid port number"
            port = int(port_str)

            self.engine: Engine = self.__setup_mysql(
                username=self._config["MYSQL_USERNAME"],
                password=self._config["MYSQL_PASSWORD"],
                hostname=self._config["MYSQL_HOSTNAME"],
                port=port,
                database=self._config["MYSQL_DATABASE"],
            )

        else:
            raise UnknownDBMSTypeError(f"Database management system (DBMS) '{self._config['DBMS']}' is unknown")

        self._SessionFactory: sessionmaker = sessionmaker(bind=self.engine)
        self.Session: scoped_session = scoped_session(self._SessionFactory)
        self.Base: DeclarativeMeta = declarative_base()

    @property
    def session(self):
        return self.Session()
