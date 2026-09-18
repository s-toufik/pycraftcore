import dataclasses

import pytest

from pycraftcore.file_handler.schema.file_manifest import FileManifest


def test_file_manifest_holds_the_given_fields():
    manifest = FileManifest(file_path="/tmp/data.txt", byte_size=42, line_count=3)

    assert manifest.file_path == "/tmp/data.txt"
    assert manifest.byte_size == 42
    assert manifest.line_count == 3


def test_file_manifest_is_a_dataclass():
    assert dataclasses.is_dataclass(FileManifest)


def test_file_manifest_is_slotted_and_rejects_new_attributes():
    manifest = FileManifest(file_path="/tmp/data.txt", byte_size=0, line_count=0)

    with pytest.raises(AttributeError):
        manifest.extra = "not allowed"
