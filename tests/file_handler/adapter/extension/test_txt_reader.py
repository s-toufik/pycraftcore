from pycraftcore.file_handler.adapter.extension.txt.txt_reader import TxtFileReader


def test_read_returns_file_contents_as_string(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello world\n")

    result = TxtFileReader.read(str(file_path))

    assert result == "hello world\n"


def test_read_returns_empty_string_for_empty_file(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    result = TxtFileReader.read(str(file_path))

    assert result == ""
