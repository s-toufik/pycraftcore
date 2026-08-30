from pycraftcore.runtime.python.schema import CodeStdout, SafeCodeSettings


def test_safe_code_settings_defaults():
    settings = SafeCodeSettings()

    assert settings.code_timeout == 10
    assert settings.max_memory_mb == 256


def test_safe_code_settings_accepts_overrides():
    settings = SafeCodeSettings(code_timeout=5, max_memory_mb=128)

    assert settings.code_timeout == 5
    assert settings.max_memory_mb == 128


def test_code_stdout_holds_stdout_and_stderr():
    result = CodeStdout(stdout="out", stderr="err")

    assert result.stdout == "out"
    assert result.stderr == "err"
