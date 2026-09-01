from dataclasses import dataclass

import pytest

from pycraftcore.serializer.adapter.dictionary_serializer import DictionarySerializer


@dataclass
class Point:
    x: int
    y: int


def test_serialize_returns_dict():
    result = DictionarySerializer.serialize(Point(x=1, y=2))

    assert result == {"x": 1, "y": 2}


def test_round_trip_preserves_data():
    original = Point(x=1, y=2)

    payload = DictionarySerializer.serialize(original)
    restored = DictionarySerializer.deserialize(payload, Point)

    assert restored == original


def test_serialize_rejects_non_dataclass_instance():
    with pytest.raises(TypeError, match="dataclass instance"):
        DictionarySerializer.serialize({"x": 1, "y": 2})


def test_serialize_rejects_dataclass_type_instead_of_instance():
    with pytest.raises(TypeError, match="dataclass instance"):
        DictionarySerializer.serialize(Point)
