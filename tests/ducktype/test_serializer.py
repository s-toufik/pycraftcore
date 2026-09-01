from pycraftcore.serializer.adapter.binary_serializer import BinarySerializer
from pycraftcore.serializer.adapter.dictionary_serializer import DictionarySerializer
from pycraftcore.serializer.adapter.json_serializer import JSONSerializer
from pycraftcore.serializer.port.serializer import Serializer


def test_binary_serializer_satisfies_serializer():
    serializer: Serializer[bytes] = BinarySerializer

    assert isinstance(serializer, Serializer)


def test_dictionary_serializer_satisfies_serializer():
    serializer: Serializer[dict] = DictionarySerializer

    assert isinstance(serializer, Serializer)


def test_json_serializer_satisfies_serializer():
    serializer: Serializer[str] = JSONSerializer

    assert isinstance(serializer, Serializer)
