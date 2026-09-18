import logging
import threading


class StandardLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__init__logger()

        return cls._instance

    def __init__logger(self):
        self._logger = logging.getLogger("pycraftcore")

    def info(self, message: str) -> None:
        self._logger.info(message, stacklevel=2)

    def warning(self, message: str) -> None:
        self._logger.warning(message, stacklevel=2)

    def error(self, message: str) -> None:
        self._logger.error(message, stacklevel=2)

    def critical(self, message: str) -> None:
        self._logger.critical(message, stacklevel=2)

    def debug(self, message: str) -> None:
        self._logger.debug(message, stacklevel=2)

    def exception(self, message: str) -> None:
        self._logger.exception(message, stacklevel=2)

    def attach(self, handler: logging.Handler) -> None:
        self._logger.addHandler(handler)
