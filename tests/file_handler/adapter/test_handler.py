import pytest

from pycraftcore.file_handler.adapter.factory import FileHandlerFactory
from pycraftcore.file_handler.adapter.handler import Handler


def test_handler_returns_factory_for_yml_path(tmp_path):
    file_path = tmp_path / "config.yml"

    factory = Handler(str(file_path))

    assert isinstance(factory, FileHandlerFactory)


def test_handler_round_trips_yml_data(tmp_path):
    file_path = tmp_path / "config.yml"

    Handler(str(file_path)).write({"name": "test", "value": 42})
    result = Handler(str(file_path)).read()

    assert result == {"name": "test", "value": 42}


def test_handler_raises_for_unsupported_extension(tmp_path):
    file_path = tmp_path / "config.foo"
    file_path.write_text("{}")

    with pytest.raises(NotImplementedError):
        Handler(str(file_path)).read()
