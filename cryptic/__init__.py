import json
import os
import socket
import threading
import time
from os import environ
from typing import Tuple, Dict, Callable, List, Union, NoReturn, Any, Optional
from uuid import uuid4
import logging

import scheme
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import sessionmaker

import sentry_sdk
from sentry_sdk import capture_exception, configure_scope


class IllegalArgumentError(ValueError):
    pass


class IllegalReturnTypeError(ValueError):
    pass


class UnknownDBMSTypeError(ValueError):
    pass


class UnknownModeError(ValueError):
    pass


class Config:
    to_load: List[Tuple[str, str]] = [
        ("MODE", "production"),
        ("DATA_LOCATION", "data/"),
        ("DBMS", "sqlite"),
        ("SQLITE_FILE", "data.db"),
        ("MYSQL_HOSTNAME", ""),  # as MYSQL_... is not the default, we don't need default values
        ("MYSQL_PORT", ""),
        ("MYSQL_DATABASE", ""),
        ("MYSQL_USERNAME", ""),
        ("MYSQL_PASSWORD", ""),
        ("RECYCLE_POOL", 1550),
        ("PATH_LOGFILE", ""),
        ("DSN", ""),  # Data Source Name ... needed for connecting to Sentry
        ("RELEASE", ""),
    ]

    def __init__(self):
        self.__config: dict = {}

        # load all configuration values from the env
        for key in Config.to_load:
            if isinstance(key, tuple):
                if key[0] in os.environ:
                    self.__config[key[0]] = os.environ.get(key[0])
                else:
                    self.__config[key[0]] = key[1]
            elif key in os.environ:
                self.__config[key] = os.environ.get(key)

    def __contains__(self, item: str):
        return item in self.__config

    def __getitem__(self, item: str) -> Optional[str]:
        if item in self:
            return self.__config[item]
        return None

    def __setitem__(self, key: str, value: Any):
        self.__config[key] = value

    def set_mode(self, mode):
        if mode.lower() in ("debug", "production"):
            self["mode"] = mode
        else:
            raise UnknownModeError(f"the mode {mode} is unknown")


_config = Config()


class Sentry(logging.Logger):
    def __init__(self, name):
        super().__init__(self, logging.INFO)
        self.__using_sentry: bool = False
        self._name: str = name
        self.__setup_logger()
        self.__setup_sentry()

    def __setup_logger(self) -> None:
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format: logging.Formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_format)

        if _config["PATH_LOGFILE"] != "" and _config["PATH_LOGFILE"][-1] == "/":

            file_handler: logging.FileHandler = logging.FileHandler(_config["PATH_LOGFILE"] + self._name + ".log")
            file_handler.setLevel(logging.DEBUG)
            file_format: logging.Formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_format)

            self.addHandler(file_handler)

        self.addHandler(console_handler)

        self.info("logger configured ...")

    def __setup_sentry(self) -> None:
        if _config["DSN"] != "":
            sentry_sdk.init(dsn=_config["DSN"], release=_config["RELEASE"])
            self.__using_sentry = True
            logging.info("Setup SDK was performed DSN:", _config["DSN"])

    def capture_exception(self, e: Exception, **kwargs) -> None:
        self.error(e, exc_info=True)
        if self.__using_sentry:
            capture_exception(e)
            with configure_scope() as scope:
                for key in kwargs:
                    scope.set_extra(key, kwargs[key])
                    # .set_context has reserved keys we use set_extra too avoid such rare case


class DatabaseWrapper:
    def __init__(self):
        if _config["MODE"] == "debug":
            _config["DBMS"] = "sqlite"
        elif _config["MODE"] == "production":
            _config["DBMS"] = "mysql"

        self.engine = None
        self.session = None
        self.Session = None
        self.Base = None
        self.connection = None

        self.setup_database()

    @staticmethod
    def __setup_sqlite(filename: str, storage_location: str = "data/") -> Engine:
        """
        :param filename: The filename
        :param storage_location: The directory the database file will be stored
        :return: Tuple[DeclarativeMeta, Any] where "Any" really is of the type sessionmaker(bind=engine)() returns
        """
        if not os.path.exists(storage_location):
            os.makedirs(storage_location)

        return create_engine("sqlite:///" + os.path.join(storage_location, filename))

    @staticmethod
    def __setup_mysql(username: str, password: str, hostname: str, port: int, database: str) -> Engine:
        assert 0 < port <= 65535, "invalid port number"
        return create_engine(
            f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}", pool_recycle=_config["RECYCLE_POOL"]
        )

    def setup_database(self) -> None:
        if _config["DBMS"] == "sqlite":
            self.engine: Engine = self.__setup_sqlite(
                filename=_config["SQLITE_FILE"], storage_location=_config["DATA_LOCATION"]
            )
        elif _config["DBMS"] == "mysql":
            port: str = _config["MYSQL_PORT"]
            if not port.isdecimal():
                # "merkste selber wo das problem liegt?"
                # thanks to google translate
                # 19:05 15.04.2019 Head Meeting
                raise Exception("in qua iacet forsit animadverto se?")
            port: int = int(port)

            self.engine: Engine = self.__setup_mysql(
                username=_config["MYSQL_USERNAME"],
                password=_config["MYSQL_PASSWORD"],
                hostname=_config["MYSQL_HOSTNAME"],
                port=port,
                database=_config["MYSQL_DATABASE"],
            )
        else:
            raise UnknownDBMSTypeError(f"the DBMS {_config['DBMS']} is unknown")

        # Because it returns a class
        # noinspection PyPep8Naming
        self.Session: sessionmaker = sessionmaker(bind=self.engine)
        # The same here
        # noinspection PyPep8Naming
        self.Base: DeclarativeMeta = declarative_base()
        self.session = self.Session()
        self.connection = self.session.connection()

    def reload(self) -> None:
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.connection = self.session.connection()

    def ping(self) -> None:
        try:
            self.connection.scalar(select([1]))
            return
        except Exception as e:
            self.reload()


class MicroService:
    SERVICE_REQUEST_MAX_TIMEOUT = 10

    def __init__(self, name: str, server_address: Tuple[str, int] = None):
        self._sentry: Sentry = Sentry(name)
        self._user_endpoints: Dict[Tuple, Callable] = {}
        self._ms_endpoints: Dict[Tuple, Callable] = {}
        self._user_endpoint_requirements: Dict[Tuple, scheme.Structure] = {}
        self._name: str = name
        self._awaiting = []
        self._data = {}
        self._database: DatabaseWrapper = DatabaseWrapper()

        if server_address is not None:
            assert len(server_address) == 2, "the server host tuple has to be like (str, int)"
            assert 0 <= server_address[1] <= 65535, "port has to be in the range of 0 - 65535"

            self._server_address: Tuple[str, int] = server_address
        else:
            # use defaults
            self._server_address: List = ["127.0.0.1", 1239]

            # overwrite if environment variable given
            if "SERVER_HOST" in environ:
                self._server_address[0] = environ["SERVER_HOST"]
            if "SERVER_PORT" in environ:
                self._server_address[1] = int(environ["SERVER_PORT"])

            # convert to tuple
            self._server_address: Tuple[str, int] = tuple(self._server_address)

        self.__sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __send(self, data: dict) -> NoReturn:
        try:
            self.__sock.send(str(json.dumps(data)).encode("utf-8"))
        except socket.error:
            self.__reconnect()
        except json.JSONDecodeError as e:
            self._sentry.info("invalid json:", str(data))
            self._sentry.capture_exception(e, data=data)

    def __connect(self) -> NoReturn:
        while True:
            try:
                self.__sock.connect(self._server_address)
                return
            except socket.error:
                time.sleep(0.5)

    def __register(self) -> NoReturn:
        self.__send({"action": "register", "name": self._name})

    def __exec(self, frame):
        if "tag" in frame and "data" in frame:
            data: dict = frame["data"]
            tag: str = frame["tag"]
            endpoint: Tuple[str, ...] = tuple(frame["endpoint"])

            if tag in self._awaiting:
                self._data[tag] = data
            else:
                if "ms" in frame:
                    if endpoint not in self._ms_endpoints:
                        self._sentry.debug("ms requested: " + str(endpoint) + " Endpoint not found")
                        self.__send({"tag": tag, "ms": frame["ms"], "data": {"error": "unknown_service"}})
                        return

                    requesting_microservice = frame["ms"]

                    self._database.ping()

                    try:
                        return_data = self._ms_endpoints[endpoint](data, requesting_microservice)

                    except Exception as e:
                        self._sentry.capture_exception(e, endpoint=endpoint, data=frame)

                        return_data = {}

                    # if the handler function does not return anything
                    if return_data is None:
                        return_data = {}
                    else:
                        if not isinstance(return_data, dict):
                            raise IllegalReturnTypeError(
                                "all handler functions are expected to return either noting or a dict."
                            )

                    self.__send({"ms": requesting_microservice, "endpoint": [], "tag": tag, "data": return_data})

                elif "user" in frame:
                    if endpoint not in self._user_endpoints:
                        self._sentry.debug("user requested: " + str(endpoint) + " Endpoint not found")
                        self.__send({"tag": tag, "user": frame["user"], "data": {"error": "unknown_service"}})
                        return

                    self._database.ping()

                    requirements: scheme.Structure = self._user_endpoint_requirements[endpoint]
                    if requirements is not None:
                        try:
                            requirements.serialize(data, "json")
                        except Exception as e:
                            self._sentry.debug("invalid input data: " + str(data))
                            self.__send({"tag": tag, "data": {"error": "invalid_input_data"}})
                            return

                    try:
                        return_data = self._user_endpoints[endpoint](data, frame["user"])
                    except Exception as e:
                        self._sentry.capture_exception(e, endpoint=endpoint, data=frame)
                        return_data = {}

                    # if the handler function does not return anything
                    if return_data is None:
                        return_data = {}
                    else:
                        if not isinstance(return_data, dict):
                            raise IllegalReturnTypeError(
                                "all handler functions are expected to return either noting or a dict."
                            )

                    self.__send({"tag": tag, "data": return_data})

    def __start(self) -> NoReturn:
        while True:
            try:
                # assume all data coming from the server is well formatted
                data: bytes = self.__sock.recv(4096)

                if len(data) == 0:
                    self.__reconnect()
                    continue

                frame: dict = json.loads(data)

                threading.Thread(target=self.__exec, args=(frame,)).start()
            except json.JSONDecodeError as e:

                self._sentry.debug("Error when trying to load json: " + str(data))
                self._sentry.capture_exception(e, data=str(data))
                continue
            except socket.error:

                self._sentry.info("Lost connection to main server ... reconnect")
                self.__reconnect()
                continue

    def __reconnect(self):
        self.__sock.close()
        self.__sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("Connection closed by server ... trying to reconnect")

        while True:
            # Tries to reastablish connection to main java server
            try:
                self.__connect()
                self.__register()
                print("Reconnected")
                break
            except socket.error as e:
                time.sleep(0.5)

    def run(self) -> NoReturn:
        self.__connect()
        self.__register()
        self.__start()

    def __endpoint(
        self,
        path: Union[List[str], Tuple[str, ...]],
        requires: Optional[scheme.Structure] = None,
        for_user_request: bool = False,
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            if isinstance(path, list):
                endpoint_path: Tuple[str, ...] = tuple(path)
            elif isinstance(path, tuple):
                endpoint_path: Tuple[str, ...] = path
            else:
                raise IllegalArgumentError("endpoint(...) expects a list or tuple as endpoint.")

            if for_user_request:
                self._user_endpoints[endpoint_path] = func
                self._user_endpoint_requirements[endpoint_path] = requires
            else:
                self._ms_endpoints[endpoint_path] = func

            def inner(*args, **kwargs) -> NoReturn:
                print("This function is not directly callable.")

            return inner

        return decorator

    def microservice_endpoint(self, path: Union[List[str], Tuple[str, ...]]) -> Callable:
        return self.__endpoint(path, None, False)

    def user_endpoint(
        self, path: Union[List[str], Tuple[str, ...]], requires: Optional[Dict[str, scheme.field.Field]]
    ) -> Callable:
        if requires is not None:
            for req in requires.values():
                req.required = True
            requirements: scheme.Structure = scheme.Structure(requires, name="/".join(path))
            return self.__endpoint(path, requirements, True)
        else:
            return self.__endpoint(path, None, True)

    def contact_microservice(self, name: str, endpoint: List[str], data: dict, uuid: Union[None, str] = None):
        # No new thread, because this should be called only from inside an endpoint
        if uuid is None:
            uuid = str(uuid4())

        self.__send({"ms": name, "data": data, "tag": uuid, "endpoint": endpoint})

        self._awaiting.append(uuid)

        time_start_waiting = time.time()

        while uuid not in self._data.keys():
            time.sleep(0.001)

            if time.time() - time_start_waiting > MicroService.SERVICE_REQUEST_MAX_TIMEOUT:
                raise TimeoutError()

        data = self._data[uuid]

        self._awaiting.remove(uuid)
        del self._data[uuid]

        return data

    def contact_user(self, user_id: str, data: dict):
        self.__send({"action": "address", "user": user_id, "data": data})

    def get_db_session(self) -> Tuple[Engine, DeclarativeMeta, Any]:
        return self._database.engine, self._database.Base, self._database.session

    def get_wrapper(self) -> "DatabaseWrapper":
        return self._database

    def check_user_uuid(self, user_uuid: str) -> bool:
        uuid: str = str(uuid4())
        self.__send({"action": "user", "data": {"user": user_uuid}, "tag": uuid})

        while uuid not in self._data.keys():
            time.sleep(0.0001)

        response: dict = self._data[uuid]

        self._awaiting.remove(uuid)
        del self._data[uuid]

        return response["valid"]

    def get_user_data(self, user_uuid: str) -> dict:
        uuid: str = str(uuid4())
        self.__send({"action": "user", "data": {"user": user_uuid}, "tag": uuid})

        while uuid not in self._data.keys():
            time.sleep(0.0001)

        response: dict = self._data[uuid]

        self._awaiting.remove(uuid)

        if response["valid"]:
            try:
                return response["data"]
            except KeyError as e:
                self._sentry.capture_exception(e, user_uuid=user_uuid)

        else:
            return {"error": "invalid_user_uuid"}


def get_config(mode: Optional[str] = None) -> Config:
    if mode:
        _config.set_mode(mode)
    return _config
