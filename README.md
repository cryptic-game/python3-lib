# python3-lib

The microservice-libary for python3 of cryptic-game.

## Quick-Start

Here are 11 lines of code for your first echo microservice:

```python
from cryptic import MicroService


def handle(endpoint, data):
    print(endpoint, data)
    return data


if __name__ == '__main__':
    m = MicroService('echo', handle)
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
