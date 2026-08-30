import threading

from loguru import logger as loguru_logger


class LoguruLogger:
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
        self._logger = loguru_logger

    def info(self, message: str) -> None:
        self._logger.opt(depth=1).info(message)

    def warning(self, message: str) -> None:
        self._logger.opt(depth=1).warning(message)

    def error(self, message: str) -> None:
        self._logger.opt(depth=1).error(message)

    def critical(self, message: str) -> None:
        self._logger.opt(depth=1).critical(message)

    def debug(self, message: str) -> None:
        self._logger.opt(depth=1).debug(message)

    def exception(self, message: str) -> None:
        self._logger.opt(depth=1).exception(message)
