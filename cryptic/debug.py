import logging

import sentry_sdk

from cryptic.config import Config


class _SentryLogRedirect:
    def __init__(self):
        self._buf = ""

    def write(self, s: str):
        self._buf += s

    def flush(self):
        sentry_sdk.capture_message(self._buf, "warning")
        self._buf = ""


class _SentryLogFilter(logging.Filter):
    def filter(self, record):
        return not (hasattr(record, "NO_SENTRY") and record.NO_SENTRY)


class Debug(logging.Logger):
    def __init__(self, name: str, config: Config):
        super().__init__(name)
        self._name = name
        self._config = config
        self.__using_sentry = False
        self.__setup_sentry()
        self.__setup_logger()

    def __setup_logger(self):
        if self._config["PATH_LOGFILE"] != "" and self._config["PATH_LOGFILE"][-1] == "/":
            file_handler = logging.FileHandler(self._config["PATH_LOGFILE"] + self._name + ".log")
            file_handler.setLevel(logging.DEBUG)
            file_format: logging.Formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_format)
            self.addHandler(file_handler)

        if self.__using_sentry:
            sentry_handler = logging.StreamHandler(_SentryLogRedirect())
            sentry_handler.setLevel(logging.WARNING)
            sentry_handler.addFilter(_SentryLogFilter())
            self.addHandler(sentry_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_format)
        self.addHandler(console_handler)

    def __setup_sentry(self):
        if self._config["DSN"] != "":
            sentry_sdk.init(
                dsn=self._config["DSN"], release=self._config["RELEASE"], server_name="cryptic-" + self._name
            )
            self.__using_sentry = True

    def capture_exception(self, e: Exception, **kwargs):
        if self.__using_sentry:
            with sentry_sdk.push_scope() as scope:
                for key in kwargs:
                    scope.set_extra(key, kwargs[key])
                sentry_sdk.capture_exception(e)

        self.exception(e, extra=dict(NO_SENTRY=True))
