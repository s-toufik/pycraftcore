from unittest.mock import MagicMock

from pycraftcore.file_handler.adapter.factory import FileHandlerFactory
from pycraftcore.file_handler.adapter.provider import FileHandlerProvider


def test_call_returns_factory_bound_to_path_and_strategy():
    strategy = MagicMock()
    provider = FileHandlerProvider(strategy)

    factory = provider("config.yml")

    assert isinstance(factory, FileHandlerFactory)
    assert factory._strategy is strategy
    assert str(factory._file_path) == "config.yml"
