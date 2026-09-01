from unittest.mock import create_autospec

import pytest

from pycraftcore.application_configuration import (
    ConfigurationReader,
)
from pycraftcore.application_configuration.adapter.load_application_configuration import (
    LoadApplicationConfiguration,
)
from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration
from pycraftcore.logger.port import Logger


@pytest.fixture
def mock_reader():
    return create_autospec(ConfigurationReader, instance=True)


@pytest.fixture
def mock_logger():
    return create_autospec(Logger, instance=True)


@pytest.fixture
def mock_config():
    return create_autospec(ApplicationConfiguration, instance=True)


@pytest.fixture
def loader(mock_reader, mock_logger):
    return LoadApplicationConfiguration(mock_reader, mock_logger)


class TestLoad:
    def test_load_calls_reader_on_every_call(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        loader.load()
        loader.load()
        loader.load()
        assert mock_reader.read.call_count == 3

    def test_load_returns_config_from_reader(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        result = loader.load()
        assert result is mock_config

    def test_load_returns_none_when_reader_returns_none(self, loader, mock_reader):
        mock_reader.read.return_value = None
        result = loader.load()
        assert result is None

    def test_load_logs_and_reraises_on_reader_exception(self, loader, mock_reader, mock_logger):
        mock_reader.read.side_effect = ValueError("connection failed")

        with pytest.raises(ValueError, match="connection failed"):
            loader.load()

        mock_logger.critical.assert_called_once()
        assert "connection failed" in mock_logger.critical.call_args[0][0]

    def test_load_retries_reader_after_previous_failure(
        self, loader, mock_reader, mock_config
    ):
        mock_reader.read.side_effect = [Exception("fail"), mock_config]

        with pytest.raises(Exception, match="fail"):
            loader.load()

        result = loader.load()

        assert result is mock_config
        assert mock_reader.read.call_count == 2
