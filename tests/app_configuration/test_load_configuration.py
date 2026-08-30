import threading
from unittest.mock import create_autospec

import pytest

from pycraftcore.app_configuration import (
    ConfigurationReader,
)
from pycraftcore.app_configuration.adapter.load_configuration import (
    LoadConfiguration,
)
from pycraftcore.app_configuration.model.configuration import AppConfiguration
from pycraftcore.logger.port import Logger


@pytest.fixture(autouse=True)
def reset_singleton():
    LoadConfiguration._instance = None
    yield
    LoadConfiguration._instance = None


@pytest.fixture
def mock_reader():
    return create_autospec(ConfigurationReader, instance=True)


@pytest.fixture
def mock_logger():
    return create_autospec(Logger, instance=True)


@pytest.fixture
def mock_config():
    return create_autospec(AppConfiguration, instance=True)


@pytest.fixture
def loader(mock_reader, mock_logger):
    return LoadConfiguration(mock_reader, mock_logger)


class TestSingleton:
    def test_same_instance_returned_on_multiple_instantiations(self, mock_reader, mock_logger):
        instance_a = LoadConfiguration(mock_reader, mock_logger)
        instance_b = LoadConfiguration(mock_reader, mock_logger)
        assert instance_a is instance_b

    def test_singleton_is_thread_safe(self, mock_reader, mock_logger):
        instances = []

        def create_instance():
            instances.append(LoadConfiguration(mock_reader, mock_logger))

        threads = [threading.Thread(target=create_instance) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(i is instances[0] for i in instances)


class TestLoad:
    def test_load_calls_reader_on_first_call(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        result = loader.load()
        mock_reader.read.assert_called_once()
        assert result is mock_config

    def test_load_returns_cached_config_on_subsequent_calls(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        loader.load()
        loader.load()
        loader.load()
        mock_reader.read.assert_called_once()

    def test_load_returns_none_and_logs_on_reader_exception(self, loader, mock_reader, mock_logger):
        mock_reader.read.side_effect = Exception("connection failed")
        result = loader.load()
        assert result is None
        mock_logger.critical.assert_called_once_with("connection failed")

    def test_load_does_not_cache_on_exception(self, loader, mock_reader, mock_logger, mock_config):
        mock_reader.read.side_effect = [Exception("fail"), mock_config]
        first = loader.load()
        second = loader.load()
        assert first is None
        assert second is mock_config
        assert mock_reader.read.call_count == 2

    def test_load_returns_none_when_reader_returns_none(self, loader, mock_reader):
        mock_reader.read.return_value = None
        result = loader.load()
        assert result is None


class TestReload:
    def test_reload_calls_reader_regardless_of_cache(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        loader.load()
        loader.reload()
        assert mock_reader.read.call_count == 2

    def test_reload_updates_cached_config(self, loader, mock_reader, mock_config):
        old_config = create_autospec(AppConfiguration, instance=True)
        new_config = mock_config
        mock_reader.read.side_effect = [old_config, new_config]

        loader.load()
        result = loader.reload()

        assert result is new_config
        assert loader._cached_config is new_config

    def test_reload_returns_new_config(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        result = loader.reload()
        assert result is mock_config

    def test_reload_is_thread_safe(self, loader, mock_reader, mock_config):
        mock_reader.read.return_value = mock_config
        errors = []

        def do_reload():
            try:
                loader.reload()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_reload) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
