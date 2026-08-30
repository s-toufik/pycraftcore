from unittest.mock import MagicMock

from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy


def make_strategy():
    reader = MagicMock()
    writer = MagicMock()
    strategy = FileHandlerStrategy({"yml": {"reader": reader, "writer": writer}})
    return strategy, reader, writer


def test_get_reader_returns_registered_reader():
    strategy, reader, _ = make_strategy()

    assert strategy.get_reader("yml") is reader


def test_get_writer_returns_registered_writer():
    strategy, _, writer = make_strategy()

    assert strategy.get_writer("yml") is writer


def test_supports_returns_true_for_registered_extension():
    strategy, _, _ = make_strategy()

    assert strategy.supports("yml") is True


def test_supports_returns_false_for_unregistered_extension():
    strategy, _, _ = make_strategy()

    assert strategy.supports("json") is False
