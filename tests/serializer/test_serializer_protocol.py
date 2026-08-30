from dataclasses import dataclass

from pycraftcore.serializer.adapter.binary_serializer import BinarySerializer
from pycraftcore.serializer.port.serializer import Serializer


@dataclass
class Point:
    x: int


def test_binary_serializer_satisfies_the_serializer_protocol():
    serializer: Serializer = BinarySerializer

    payload = serializer.serialize(Point(x=1))
    restored = serializer.deserialize(payload, Point)

    assert restored == Point(x=1)
