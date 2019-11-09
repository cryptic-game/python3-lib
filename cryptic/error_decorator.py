from functools import wraps
from typing import Callable, Union, Any


class MicroserviceException(Exception):
    def __init__(self, error: dict):
        self.error: dict = error


def register_errors(*errors: Callable) -> Callable[[Callable], Callable[[dict, str], dict]]:
    def deco(f: Callable) -> Callable[[dict, str], dict]:
        @wraps(f)
        def inner(data: dict, user: str) -> dict:
            args: tuple = (data, user)
            for func in errors:
                try:
                    result: Union[tuple, Any] = func(*args)
                except MicroserviceException as exception:
                    return exception.error

                if not isinstance(result, tuple):
                    result: tuple = (result,)
                args: tuple = (data, user, *result)

            return f(*args)

        inner.__errors__ = errors

        return inner

    return deco
