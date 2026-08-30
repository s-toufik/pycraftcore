from dataclasses import dataclass

from pycraftcore.serializer.adapter.json_serializer import JSONSerializer


@dataclass
class Point:
    x: int
    y: int


def test_serialize_returns_json_string():
    result = JSONSerializer.serialize(Point(x=1, y=2))

    assert result == '{"x": 1, "y": 2}'


def test_round_trip_preserves_data():
    original = Point(x=1, y=2)

    payload = JSONSerializer.serialize(original)
    restored = JSONSerializer.deserialize(payload, Point)

    assert restored == original
