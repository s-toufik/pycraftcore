import orjson

from pycraftcore.file_handler.adapter.extension.json.json_writer import JsonFileWriter


def test_write_serializes_dict_to_json_file(tmp_path):
    file_path = tmp_path / "config.json"

    JsonFileWriter.write(str(file_path), {"name": "test", "value": 42})

    assert orjson.loads(file_path.read_bytes()) == {"name": "test", "value": 42}
