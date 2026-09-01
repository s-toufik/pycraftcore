from dataclasses import dataclass

import pytest

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


def test_serialize_rejects_non_dataclass_instance():
    with pytest.raises(TypeError, match="dataclass instance"):
        BinarySerializer.serialize({"x": 1, "y": 2})


def test_serialize_rejects_dataclass_type_instead_of_instance():
    with pytest.raises(TypeError, match="dataclass instance"):
        BinarySerializer.serialize(Point)
