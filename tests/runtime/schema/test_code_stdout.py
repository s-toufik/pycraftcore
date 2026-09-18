from pycraftcore.runtime.schema.code_stdout import CodeStdout


def test_code_stdout_holds_stdout_and_stderr():
    result = CodeStdout(stdout="out", stderr="err")

    assert result.stdout == "out"
    assert result.stderr == "err"
