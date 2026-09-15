from pycraftcore.file_handler.adapter.extension.txt.txt_writer import TxtFileWriter


def test_write_writes_string_to_file(tmp_path):
    file_path = tmp_path / "notes.txt"

    TxtFileWriter.write(str(file_path), "hello world")

    assert file_path.read_text(encoding="utf-8") == "hello world"


def test_write_overwrites_existing_file_contents(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("old content")

    TxtFileWriter.write(str(file_path), "new content")

    assert file_path.read_text(encoding="utf-8") == "new content"
