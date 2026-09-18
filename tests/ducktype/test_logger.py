from pycraftcore.logger.adapter.loguru_logger import LoguruLogger
from pycraftcore.logger.adapter.standard_logger import StandardLogger
from pycraftcore.logger.port.log_sink import LogSink
from pycraftcore.logger.port.logger import Logger


def test_loguru_logger_satisfies_logger():
    logger: Logger = LoguruLogger()

    assert isinstance(logger, Logger)


def test_loguru_logger_satisfies_log_sink():
    logger: LogSink = LoguruLogger()

    assert isinstance(logger, LogSink)


def test_standard_logger_satisfies_logger():
    logger: Logger = StandardLogger()

    assert isinstance(logger, Logger)


def test_standard_logger_satisfies_log_sink():
    logger: LogSink = StandardLogger()

    assert isinstance(logger, LogSink)
