from pycraftcore.logger.adapter.loguru_logger import LoguruLogger
from pycraftcore.logger.port.logger import Logger


def test_loguru_logger_satisfies_logger():
    logger: Logger = LoguruLogger()

    assert isinstance(logger, Logger)
