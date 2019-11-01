# python3-lib

The library that is used for microservices of the backend for the Cryptic game that are written in Python.

PyPI package: https://pypi.org/project/cryptic-game/

## Installation:

```bash
$ pip3 install cryptic-game
```

## Features

- Endpoint mapping
- Automatic input validation
- Database control with SQLAlchemy
- Automatic error capturing with Sentry and a logger

## Quick Start

Checkout [example.py](https://github.com/cryptic-game/python3-lib/blob/master/example.py) 
for a quick example on how this library is used.

## Requirements

Required are all modules in the `requirements.txt` (which will automatically be installed by pip).

## Environment Variables

| Variable            | Functionality                                                  |
|---------------------|----------------------------------------------------------------|
| MODE                | Available: debug and production                                |
| SERVER_HOST         | Hostname of the main server                                    |
| SERVER_PORT         | Microservice communication port of the main server             |
| DATA_LOCATION       | SQLite database file location                                  |
| DBMS                | Database management system; Available: mysql and sqlite        |
| SQLITE_FILE         | Name of the SQLite database file (only used if DBMS is sqlite) |
| MYSQL_HOSTNAME      | Hostname of the MySQL server                                   |
| MYSQL_PORT          | Port of the MySQL server                                       |
| MYSQL_DATABASE      | Name of the MySQL database to use                              |
| MYSQL_USERNAME      | MySQL username to use                                          |
| MYSQL_PASSWORD      | The password of the MySQL user                                 |
| PATH_LOGFILE        | Path where your log-files will be stored to                    |
| DSN                 | "Data Source Name" of your Sentry instance                     |
| RELEASE             | The release that will be reported to Sentry                    |


## Test it!

Your microservice will be supported by the [game-server of cryptic](https://github.com/cryptic-game/server).

## Wiki

Visit our [wiki](https://github.com/cryptic-game/python3-lib/wiki) for more information.
