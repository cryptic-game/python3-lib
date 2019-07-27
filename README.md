# python3-lib

The microservice-libary for python3 of cryptic-game.

Pypi Seite: https://pypi.org/project/cryptic-game/

## Installation:

```bash
$ pip3 install cryptic-game
```

## Features

- Endpoint Mapping
- automatic input validation
- Database Control
- Sentry and Logger -> Stacktraces and given Data

## Quick Start

Checkout the [example.py](https://github.com/cryptic-game/python3-lib/blob/master/example.py) for an quick example how this library is used.

## Requirements

Required are all modules in the `requirements.txt`.

## Enviroment Variables

| Variable                      | Functionality                                                 |
|-------------------------------|---------------------------------------------------------------|
| MODE                          | debug or production                                           |
| DATA_LOCATION                 | Path where you sqlite db should be stored under debug mode    |
| DBMS                          | Mysql or sqlite used internaly                                |
| SQLITE_FILE                   | Name of your sqlite db                                        |
| MYSQL_HOSTNAME                | Host where your mysql server runs                             |
| MYSQL_PORT                    | Under which port your mysql on the given host runs            |
| MYSQL_DATABASE                | Name of your mysql database                                   |
| MYSQL_USERNAME                | Mysql username                                                |
| MYSQL_PASSWORD                | Your password for this given user                             |
| PATH_LOGFILE                  | Path too where your logging files should be stored            |
| DSN                           | Data Structure Name for your sentry instance                  |
| RELEASE                       | The Release this will be reported too sentry                  |


## Test it!

Your microservice will be supported by the [game-server of cryptic](https://github.com/cryptic-game/server).

## Wiki

Visit our [wiki](https://github.com/cryptic-game/python3-lib/wiki) for more information.
