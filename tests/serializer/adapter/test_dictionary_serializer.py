from dataclasses import dataclass

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
