from unittest.mock import MagicMock

import pytest

from pycraftcore.file_handler.adapter.factory import FileHandlerFactory


def make_factory(file_path, extension_supported=True, reader=None, writer=None):
    strategy = MagicMock()
    strategy.supports.return_value = extension_supported
    strategy.get_reader.return_value = reader
    strategy.get_writer.return_value = writer
    return FileHandlerFactory(file_path, strategy), strategy


def test_read_raises_when_file_does_not_exist(tmp_path):
    factory, _ = make_factory(str(tmp_path / "missing.yml"))

    with pytest.raises(FileNotFoundError):
        factory.read()


def test_read_raises_when_extension_unsupported(tmp_path):
    file_path = tmp_path / "config.txt"
    file_path.write_text("data")
    factory, _ = make_factory(str(file_path), extension_supported=False)

    with pytest.raises(NotImplementedError):
        factory.read()


def test_read_delegates_to_strategy_reader(tmp_path):
    file_path = tmp_path / "config.yml"
    file_path.write_text("data")
    reader = MagicMock()
    reader.read.return_value = {"ok": True}
    factory, strategy = make_factory(str(file_path), reader=reader)

    result = factory.read()

    strategy.get_reader.assert_called_once_with("yml")
    reader.read.assert_called_once_with(str(file_path))
    assert result == {"ok": True}


def test_write_raises_when_parent_directory_missing():
    factory, _ = make_factory("/no/such/directory/config.yml")

    with pytest.raises(FileNotFoundError):
        factory.write({"a": 1})


def test_write_raises_when_extension_unsupported(tmp_path):
    file_path = tmp_path / "config.txt"
    factory, _ = make_factory(str(file_path), extension_supported=False)

    with pytest.raises(NotImplementedError):
        factory.write({"a": 1})


def test_write_delegates_to_strategy_writer(tmp_path):
    file_path = tmp_path / "config.yml"
    writer = MagicMock()
    factory, strategy = make_factory(str(file_path), writer=writer)

    factory.write({"a": 1})

    strategy.get_writer.assert_called_once_with("yml")
    writer.write.assert_called_once_with(str(file_path), {"a": 1})
