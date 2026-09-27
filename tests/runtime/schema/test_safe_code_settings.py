from pycraftcore.runtime.schema.safe_code_settings import SafeCodeSettings


def test_safe_code_settings_defaults():
    settings = SafeCodeSettings()

    assert settings.code_timeout == 10
    assert settings.max_memory_mb == 256
    assert settings.working_directory is None


def test_safe_code_settings_accepts_overrides():
    settings = SafeCodeSettings(code_timeout=5, max_memory_mb=128, working_directory="/work")

    assert settings.code_timeout == 5
    assert settings.max_memory_mb == 128
    assert settings.working_directory == "/work"
