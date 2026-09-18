import logging
from unittest.mock import MagicMock, patch

from pycraftcore.logger.adapter.standard_logger import StandardLogger


def reset_singleton() -> None:
    StandardLogger._instance = None


def test_is_a_singleton():
    reset_singleton()
    try:
        first = StandardLogger()
        second = StandardLogger()

        assert first is second
    finally:
        reset_singleton()


def test_delegates_each_level_to_standard_logging_with_stacklevel_two():
    reset_singleton()
    try:
        fake_logger = MagicMock(spec=logging.Logger)

        with patch(
            "pycraftcore.logger.adapter.standard_logger.logging.getLogger",
            return_value=fake_logger,
        ):
            logger = StandardLogger()

            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")
            logger.debug("debug message")
            logger.exception("exception message")

        fake_logger.info.assert_called_once_with("info message", stacklevel=2)
        fake_logger.warning.assert_called_once_with("warning message", stacklevel=2)
        fake_logger.error.assert_called_once_with("error message", stacklevel=2)
        fake_logger.critical.assert_called_once_with("critical message", stacklevel=2)
        fake_logger.debug.assert_called_once_with("debug message", stacklevel=2)
        fake_logger.exception.assert_called_once_with("exception message", stacklevel=2)
    finally:
        reset_singleton()
