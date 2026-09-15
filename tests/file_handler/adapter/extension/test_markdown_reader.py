from pycraftcore.file_handler.adapter.extension.markdown.markdown_reader import MarkdownFileReader


def test_read_returns_file_contents_as_string(tmp_path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("# Title\n\nSome text\n")

    result = MarkdownFileReader.read(str(file_path))

    assert result == "# Title\n\nSome text\n"


def test_read_returns_empty_string_for_empty_file(tmp_path):
    file_path = tmp_path / "empty.md"
    file_path.write_text("")

    result = MarkdownFileReader.read(str(file_path))

    assert result == ""
