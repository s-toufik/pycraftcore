from pycraftcore.logger.adapter.standard_logger import StandardLogger
from pycraftcore.logger.port.logger import Logger


def test_standard_logger_satisfies_logger():
    logger: Logger = StandardLogger()

    assert isinstance(logger, Logger)
