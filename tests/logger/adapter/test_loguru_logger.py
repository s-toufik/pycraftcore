from unittest.mock import MagicMock, patch

from pycraftcore.logger.adapter.loguru_logger import LoguruLogger


def reset_singleton() -> None:
    LoguruLogger._instance = None


def test_is_a_singleton():
    reset_singleton()
    try:
        first = LoguruLogger()
        second = LoguruLogger()

        assert first is second
    finally:
        reset_singleton()


def test_delegates_each_level_to_loguru_with_depth_one():
    reset_singleton()
    try:
        fake_loguru = MagicMock()
        fake_opt = MagicMock()
        fake_loguru.opt.return_value = fake_opt

        with patch("pycraftcore.logger.adapter.loguru_logger.loguru_logger", fake_loguru):
            logger = LoguruLogger()

            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")
            logger.debug("debug message")
            logger.exception("exception message")

        assert fake_loguru.opt.call_args_list == [((), {"depth": 1})] * 6
        fake_opt.info.assert_called_once_with("info message")
        fake_opt.warning.assert_called_once_with("warning message")
        fake_opt.error.assert_called_once_with("error message")
        fake_opt.critical.assert_called_once_with("critical message")
        fake_opt.debug.assert_called_once_with("debug message")
        fake_opt.exception.assert_called_once_with("exception message")
    finally:
        reset_singleton()
