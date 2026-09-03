import yaml

from pycraftcore.file_handler.adapter.extension.yml.yml_writer import YmlFileWriter


def test_write_serializes_dict_to_yml_file(tmp_path):
    file_path = tmp_path / "config.yml"

    YmlFileWriter.write(str(file_path), {"name": "test", "value": 42})

    assert yaml.safe_load(file_path.read_text()) == {"name": "test", "value": 42}
