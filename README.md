# python3-lib

The microservice-libary for python3 of cryptic-game.

Pypi Seite: https://pypi.org/project/cryptic-game/

## Installation:

```bash
$ pip3 install cryptic-game
```

## Quick Start

```python
from cryptic import MicroService, get_config, Config
from uuid import uuid4
from sqlalchemy import Column, String
from typing import Union

config: Config = get_config("debug")  # this sets config to debug mode
ms: MicroService = MicroService(name="echo")
db_wrapper = ms.get_wrapper()


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    print(data, microservice)
    return {}


@ms.user_endpoint(path=["user"])
def handle(data: dict, user: str):
    print(data, user)
    return {}


class Test(db_wrapper.Base):
    __tablename__: str = 'test'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    name: Union[Column, str] = Column(String(255), nullable=False)

    @staticmethod
    def create(name: str) -> 'Test':
        my_test: Test = Test(uuid=str(uuid4()), name=name)

        return my_test


if __name__ == '__main__':
    ms.run()
```

## Requirements

Required are all modules in the `requirements.txt`.

## Test it!

Your microservice will be supported by the [game-server of cryptic](https://github.com/cryptic-game/server).

### Environment variables

| key               | default value |
|-------------------|---------------|
| SERVER_HOST       | 127.0.0.1     |
| SERVER_PORT       | 1239          |

## Wiki

Visit our [wiki](https://github.com/cryptic-game/python3-lib/wiki) for more information.
