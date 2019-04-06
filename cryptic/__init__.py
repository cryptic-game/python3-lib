import json
import socket
import threading
import time
from os import environ
from typing import Tuple, Dict, Callable, List, Union, NoReturn
from uuid import uuid4


class IllegalArgumentError(ValueError):
    pass


class IllegalReturnTypeError(ValueError):
    pass


class MicroService:
    SERVICE_REQUEST_MAX_TIMEOUT = 10

    def __init__(self, name: str, server_address: Tuple[str, int] = None):
        self._user_endpoints: Dict[Tuple, Callable] = {}
        self._ms_endpoints: Dict[Tuple, Callable] = {}
        self._name: str = name
        self._awaiting = []
        self._data = {}

        if server_address is not None:
            assert len(server_address) == 2, "the server host tuple has to be like (str, int)"
            assert 0 <= server_address[1] <= 65535, "port has to be in the range of 0 - 65535"

            self._server_address: Tuple[str, int] = server_address
        else:
            # use defaults
            self._server_address: List = ['127.0.0.1', 1239]

            # overwrite if environment variable given
            if 'SERVER_HOST' in environ:
                self._server_address[0] = environ['SERVER_HOST']
            if 'SERVER_PORT' in environ:
                self._server_address[1] = int(environ['SERVER_PORT'])

            # convert to tuple
            self._server_address: Tuple[str, int] = tuple(self._server_address)

        self.__sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __send(self, data: dict) -> NoReturn:
        self.__sock.send(str(json.dumps(data)).encode("utf-8"))

    def __connect(self) -> NoReturn:
        self.__sock.connect(self._server_address)

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
                        # MAYBE add sentry here
                        self.__send({
                            "tag": tag,
                            "user": frame["user"],
                            "data": {
                                "error": "unknown service"
                            }
                        })
                        return

                    requesting_microservice = frame["ms"]

                    return_data = self._ms_endpoints[endpoint](data, requesting_microservice)

                    # if the handler function does not return anything
                    if return_data is None:
                        return_data = {}
                    else:
                        if not isinstance(return_data, dict):
                            raise IllegalReturnTypeError(
                                "all handler functions are expected to return either noting or a dict.")

                    self.__send({
                        "ms": requesting_microservice,
                        "endpoint": [],
                        "tag": tag,
                        "data": return_data
                    })
                elif "user" in frame:
                    if endpoint not in self._user_endpoints:
                        # MAYBE add sentry here
                        self.__send({
                            "tag": tag,
                            "user": frame["user"],
                            "data": {
                                "error": "unknown service"
                            }
                        })
                        return

                    return_data = self._user_endpoints[endpoint](data, frame["user"])

                    # if the handler function does not return anything
                    if return_data is None:
                        return_data = {}
                    else:
                        if not isinstance(return_data, dict):
                            raise IllegalReturnTypeError(
                                "all handler functions are expected to return either noting or a dict.")

                    self.__send({
                        "tag": tag,
                        "data": return_data
                    })

    def __start(self) -> NoReturn:
        while True:
            try:
                # assume all data coming from the server is well formatted
                frame: dict = json.loads(self.__sock.recv(4096))

                threading.Thread(target=self.__exec, args=(frame,)).start()
            except json.JSONDecodeError:
                # TODO theoretically sentry here
                continue

    def run(self) -> NoReturn:
        self.__connect()
        self.__register()
        self.__start()

    def __endpoint(self, path: Union[List[str], Tuple[str, ...]], for_user_request: bool = False) -> Callable:
        def decorator(func: Callable) -> Callable:
            if isinstance(path, list):
                endpoint_path: Tuple[str, ...] = tuple(path)
            elif isinstance(path, tuple):
                endpoint_path: Tuple[str, ...] = path
            else:
                raise IllegalArgumentError("endpoint(...) expects a list or tuple as endpoint.")

            if for_user_request:
                self._user_endpoints[endpoint_path] = func
            else:
                self._ms_endpoints[endpoint_path] = func

            def inner(*args, **kwargs) -> NoReturn:
                print("This function is not directly callable.")

            return inner

        return decorator

    def microservice_endpoint(self, path: Union[List[str], Tuple[str, ...]]) -> Callable:
        return self.__endpoint(path, False)

    def user_endpoint(self, path: Union[List[str], Tuple[str, ...]]) -> Callable:
        return self.__endpoint(path, True)

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
        self.__send({
            "action": "address",
            "user": user_id,
            "data": data
        })
