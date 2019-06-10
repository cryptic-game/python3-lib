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
from scheme import *

config: Config = get_config("debug")  # this sets config to debug mode
ms: MicroService = MicroService(name="echo")
wrapper = ms.get_wrapper()

user_device: dict = {
    'user_uuid': Text(nonempty=True),
    'device_uuid': Email(nonempty=True),
    'active': Boolean(required=True, default=True),
    'somedata': Integer(minimum=0, default=0),
}
# just giving an empty dictionary will be interpreted as no validation required.


@ms.microservice_endpoint(path=["microservice"])
def handle(data: dict, microservice: str):
    return {"name": data["yourname"]}


@ms.user_endpoint(path=["user"], requires=user_device)
def handle(data: dict, user: str):
    # Input is now already validated
    print(data["username"])
    return {"ok": True}


if __name__ == '__main__':
    ms.run()


class Test(wrapper.Base):
    __tablename__: str = 'test'

    uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    name: Union[Column, str] = Column(String(255), nullable=False)

    @staticmethod
    def create(name: str) -> 'Test':
        my_test: Test = Test(uuid=str(uuid4()), name=name)
        
        wrapper.session.add(my_test)
        wrapper.session.commit()

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
