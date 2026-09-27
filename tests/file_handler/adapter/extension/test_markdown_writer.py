from pycraftcore.file_handler.adapter.extension.markdown.markdown_writer import MarkdownFileWriter


def test_write_writes_data_to_file(tmp_path):
    file_path = tmp_path / "notes.md"

    MarkdownFileWriter.write(str(file_path), "# Title\n\nSome text")

    assert file_path.read_text(encoding="utf-8") == "# Title\n\nSome text"


def test_write_writes_empty_string_when_data_is_empty(tmp_path):
    file_path = tmp_path / "notes.md"

    MarkdownFileWriter.write(str(file_path), "")

    assert file_path.read_text(encoding="utf-8") == ""
