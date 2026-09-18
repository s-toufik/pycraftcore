import pytest

from pycraftcore.file_handler.enum.read_chunk_mode import ReadChunkMode
from pycraftcore.file_handler.port.reader import Reader
from pycraftcore.file_handler.port.writer import Writer


class FullTextReader(Reader):
    @staticmethod
    def _read_full(file_path: str):
        with open(file_path, encoding="utf-8") as file:
            return file.read()


def test_reader_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Reader()


def test_writer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Writer()


def test_read_defaults_to_full_read_when_no_chunk_mode_given(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\nline3\n")

    result = FullTextReader.read(str(file_path))

    assert result == "line1\nline2\nline3\n"


def test_read_returns_all_lines_in_line_mode_when_no_bounds_given(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\nline3\n")

    result = FullTextReader.read(str(file_path), read_chunk_mode=ReadChunkMode.LINE)

    assert result == ["line1\n", "line2\n", "line3\n"]


def test_read_line_chunk_respects_start_offset(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\nline3\n")

    result = FullTextReader.read(str(file_path), read_chunk_mode=ReadChunkMode.LINE, start=1)

    assert result == ["line2\n", "line3\n"]


def test_read_line_chunk_respects_count(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\nline3\n")

    result = FullTextReader.read(str(file_path), read_chunk_mode=ReadChunkMode.LINE, count=2)

    assert result == ["line1\n", "line2\n"]


def test_read_line_chunk_respects_start_and_count_together(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\nline3\nline4\n")

    result = FullTextReader.read(
        str(file_path), read_chunk_mode=ReadChunkMode.LINE, start=1, count=2
    )

    assert result == ["line2\n", "line3\n"]


def test_read_line_chunk_returns_empty_list_when_start_beyond_end_of_file(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("line1\nline2\n")

    result = FullTextReader.read(str(file_path), read_chunk_mode=ReadChunkMode.LINE, start=10)

    assert result == []
