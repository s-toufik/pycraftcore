import pytest

from pycraftcore.file_handler.port.reader import Reader
from pycraftcore.file_handler.port.writer import Writer


def test_reader_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Reader()


def test_writer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Writer()
