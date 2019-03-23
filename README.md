# python3-lib

The microservice-libary for python3 of cryptic-game.

Pypi Seite: https://pypi.org/project/microservicecryp/

## Installation:

```bash
$ pip3 install microservicecryp
```

## Quick-Start

Here are 15 lines of code for your first echo microservice:

```python
from cryptic import MicroService


def handle(endpoint, data):
    print(endpoint, data)
    return data


def handle_ms(ms, data):
    print(ms, data)


if __name__ == '__main__':
    m = MicroService('echo', handle, handle_ms, True)
    m.run()
```

## Requirements

Required are all modules in the `requirements.txt`.

## Test it!

Your microservice will be supported by the [game-server of cryptic](https://github.com/cryptic-game/server).

### Environment variables

| key               | default value |
|-------------------|---------------|
| MSSOCKET_HOST     | 127.0.0.1     |
| MSSOCKET_PORT     | 1239          |

## Wiki

Visit our [wiki](https://github.com/cryptic-game/python3-lib/wiki) for more information.
