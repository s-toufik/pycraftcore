import json

import pytest

from pycraftcore.runtime.schema.code_result import CodeResult


def test_from_stdout_parses_the_result_envelope():
    result = CodeResult.from_stdout(json.dumps({"__type__": "int", "result": 4}))

    assert result == CodeResult(type_name="int", value=4, printed="")


def test_from_stdout_keeps_what_the_code_printed_before_the_envelope():
    stdout = "first\nsecond\n" + json.dumps({"__type__": "dict", "result": {"a": 1}})

    result = CodeResult.from_stdout(stdout)

    assert result.value == {"a": 1}
    assert result.printed == "first\nsecond"


def test_from_stdout_rejects_output_without_an_envelope():
    with pytest.raises(json.JSONDecodeError):
        CodeResult.from_stdout("no envelope here")
