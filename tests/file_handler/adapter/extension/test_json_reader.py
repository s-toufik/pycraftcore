from pycraftcore.file_handler.adapter.extension.json.json_reader import JsonFileReader


def test_read_parses_json_file_into_dict(tmp_path):
    file_path = tmp_path / "config.json"
    file_path.write_text('{"name": "test", "value": 42}')

    result = JsonFileReader.read(str(file_path))

    assert result == {"name": "test", "value": 42}
