import json
import socket
import threading
import time
from typing import Tuple, Dict, Callable, Union, List, Optional

import scheme
from uuid import uuid4

from cryptic.config import Config
from cryptic.errors import FrameCorruptedError, FrameTooLongError, IllegalReturnTypeError
from cryptic.database import DatabaseWrapper
from cryptic.debug import Debug
from cryptic.jsonreader import JSONReader


class MicroService:
    SERVICE_REQUEST_MAX_TIMEOUT = 10

    def __init__(self, name: str, server_address: Tuple[str, int] = None):
        self.config = Config()
        self.debug = Debug(name, self.config)
        self.name = name
        self._user_endpoints: Dict[Tuple, Callable] = {}
        self._ms_endpoints: Dict[Tuple, Callable] = {}
        self._user_endpoint_requirements: Dict[Tuple, scheme.Structure] = {}
        self._awaiting = []
        self._data = {}
        self._database: DatabaseWrapper = DatabaseWrapper(self.config)
        self._json_reader: JSONReader = JSONReader()

        if server_address is not None:
            assert len(server_address) == 2, "Invalid address; has to be tuple of str and int"
            assert 0 <= server_address[1] <= 65535, "Invalid port number"

            self._server_address: Tuple[str, int] = server_address
        else:
            port_str = self.config["SERVER_PORT"]
            assert port_str.isdecimal(), "Invalid port number"
            port = int(port_str)

            self._server_address: Tuple[str, int] = (self.config["SERVER_HOST"], port)

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.__connect()
        self.__register()
        self.__start()

    def __connect(self):
        while True:
            try:
                self.__sock.connect(self._server_address)
                self.debug.info(f"Connected to {self._server_address[0]}:{self._server_address[1]}")
                return
            except socket.error:
                time.sleep(0.5)

    def __reconnect(self):
        self.__sock.close()
        self.__sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.debug.info("Connection closed by server. Trying to reconnect")

        while True:
            # Try to reestablish the connection to the main java server
            try:
                self.__connect()
                self.__register()
                self.debug.info("Reconnected")
                break
            except socket.error:
                time.sleep(0.5)

    def __send(self, data: dict):
        try:
            self.__sock.send(str(json.dumps(data)).encode("utf-8"))
        except socket.error:
            self.__reconnect()
        except json.JSONDecodeError as e:
            self.debug.info("Invalid json: ", str(data))
            self.debug.capture_exception(e, data=data)

    def __register(self):
        self.__send({"action": "register", "name": self.name})

    def __start(self):
        while True:
            data: bytes = b""
            try:
                data = self.__sock.recv(4096)

                if len(data) == 0:
                    self.__reconnect()
                    continue

                objects = self._json_reader.next(data)

                for obj in objects:
                    try:
                        frame: dict = json.loads(obj)
                        threading.Thread(target=self.__exec, args=(frame,)).start()
                    except json.JSONDecodeError as e:
                        self.debug.debug("Error when trying to load json: " + str(data))
                        self.debug.capture_exception(e, data=str(data))
                        continue

            except (FrameCorruptedError, FrameTooLongError) as e:
                self.debug.debug("Error when trying to load json: " + str(data))
                self.debug.capture_exception(e, data=str(data))
                continue
            except socket.error:
                self.debug.info("Lost connection to main server ... reconnect")
                self.__reconnect()
                continue

    def __exec(self, frame):
        if not ("tag" in frame and "data" in frame) or not (
            isinstance(frame["tag"], str) and isinstance(frame["data"], dict)
        ):
            self.debug.warning(f"Got an unknown request: {json.dumps(frame)}")
            return

        data: dict = frame["data"]
        tag: str = frame["tag"]
        endpoint: Tuple[str, ...] = tuple(frame["endpoint"]) if "endpoint" in frame else None

        if tag in self._awaiting:
            self._data[tag] = data
        else:
            if "ms" in frame:  # Request from a microservice
                if endpoint not in self._ms_endpoints:
                    self.debug.debug(f"(Microservice requested): '{str(endpoint)}' endpoint not found")
                    self.__send({"tag": tag, "ms": frame["ms"], "data": {"error": "unknown_endpoint"}})
                    return

                requesting_microservice = frame["ms"]

                try:
                    return_data = self._ms_endpoints[endpoint](data, requesting_microservice)
                    if return_data is None:
                        return_data = {}
                    elif not isinstance(return_data, dict):
                        raise IllegalReturnTypeError("All endpoint functions must return either nothing or a dict")
                except Exception as e:
                    self.debug.capture_exception(e, endpoint=endpoint, data=frame)
                    return_data = {}
                finally:
                    self._database.Session.remove()

                self.__send({"ms": requesting_microservice, "endpoint": [], "tag": tag, "data": return_data})

            elif "user" in frame:  # Request from a user
                if endpoint not in self._user_endpoints:
                    self.debug.debug(f"(User requested): '{str(endpoint)}' endpoint not found")
                    self.__send({"tag": tag, "user": frame["user"], "data": {"error": "unknown_endpoint"}})
                    return

                requirements: scheme.Structure = self._user_endpoint_requirements[endpoint]
                if requirements is not None:
                    # noinspection PyBroadException
                    try:
                        requirements.serialize(data, "json")
                    except Exception:
                        self.debug.debug(f"Invalid input data: {str(data)}")
                        self.__send({"tag": tag, "data": {"error": "invalid_input_data"}})
                        return

                try:
                    return_data = self._user_endpoints[endpoint](data, frame["user"])
                    if return_data is None:
                        return_data = {}
                    elif not isinstance(return_data, dict):
                        raise IllegalReturnTypeError("All endpoint functions must return either nothing or a dict")
                except Exception as e:
                    self.debug.capture_exception(e, endpoint=endpoint, data=frame)
                    return_data = {}
                finally:
                    self._database.Session.remove()

                self.__send({"tag": tag, "data": return_data})

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
                raise TypeError("endpoint(...) expects a list or tuple as endpoint")

            if for_user_request:
                self._user_endpoints[endpoint_path] = func
                self._user_endpoint_requirements[endpoint_path] = requires
            else:
                self._ms_endpoints[endpoint_path] = func

            # noinspection PyUnusedLocal
            def inner(*args, **kwargs):
                raise NotImplementedError("This function is not directly callable")

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

    def get_wrapper(self) -> "DatabaseWrapper":
        return self._database

    # Endpoint utility functions (should only be called inside an endpoint)

    def contact_microservice(self, name: str, endpoint: List[str], data: dict, uuid: Union[None, str] = None):
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

    def get_user_data(self, user_uuid: str) -> dict:
        uuid: str = str(uuid4())
        self._awaiting.append(uuid)
        self.__send({"action": "user", "data": {"user": user_uuid}, "tag": uuid})

        while uuid not in self._data.keys():
            time.sleep(0.0001)

        response: dict = self._data[uuid]

        self._awaiting.remove(uuid)

        return response

    def check_user_uuid(self, user_uuid: str) -> bool:
        return self.get_user_data(user_uuid)["valid"]
