import os


class Config:
    DEFAULT_VALUES = {
        "MODE": "production",  # Available: debug and production
        "SERVER_HOST": "127.0.0.1",  # Hostname of the main server
        "SERVER_PORT": "1239",  # Port of the main server
        "DATA_LOCATION": "data/",
        "DBMS": "mysql",  # Available: mysql and sqlite
        "SQLITE_FILE": "data.db",  # Filename of the sqlite database if DBMS is sqlite
        "MYSQL_HOSTNAME": "",  # As MySQL is not the default, we don't need default values
        "MYSQL_PORT": "",
        "MYSQL_DATABASE": "",
        "MYSQL_USERNAME": "",
        "MYSQL_PASSWORD": "",
        "PATH_LOGFILE": "./",
        "DSN": "",  # Data Source Name; needed for connecting to Sentry
        "RELEASE": "",  # The release that will be reported to Sentry
    }

    def __init__(self):
        self.__config = {}
        for key, default in self.DEFAULT_VALUES.items():
            if key in os.environ:
                self.__config[key] = os.environ[key]
            else:
                self.__config[key] = default

    def __contains__(self, key):
        return key in self.__config

    def __getitem__(self, key):
        if key in self.__config:
            return self.__config[key]
        return None

    def __setitem__(self, key, value):
        self.__config[key] = value
