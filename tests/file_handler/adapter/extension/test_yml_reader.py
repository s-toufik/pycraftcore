from pycraftcore.file_handler.adapter.extension.yml.yml_reader import YmlFileReader


def test_read_parses_yml_file_into_dict(tmp_path):
    file_path = tmp_path / "config.yml"
    file_path.write_text("name: test\nvalue: 42\n")

    result = YmlFileReader.read(str(file_path))

    assert result == {"name": "test", "value": 42}


def test_read_returns_none_for_empty_file(tmp_path):
    file_path = tmp_path / "empty.yml"
    file_path.write_text("")

    result = YmlFileReader.read(str(file_path))

    assert result is None
