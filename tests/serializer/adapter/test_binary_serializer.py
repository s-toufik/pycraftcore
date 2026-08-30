from dataclasses import dataclass

from pycraftcore.serializer.adapter.binary_serializer import BinarySerializer


@dataclass
class Point:
    x: int
    y: int


def test_serialize_returns_bytes():
    result = BinarySerializer.serialize(Point(x=1, y=2))

    assert isinstance(result, bytes)


def test_round_trip_preserves_data():
    original = Point(x=1, y=2)

    payload = BinarySerializer.serialize(original)
    restored = BinarySerializer.deserialize(payload, Point)

    assert restored == original
