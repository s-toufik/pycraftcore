import os

import pytest

from pycraftcore.profiler.profiled import profiled


@pytest.mark.asyncio
async def test_profiled_returns_wrapped_function_result(tmp_path):
    output_path = str(tmp_path / "profile.html")

    @profiled(output_path=output_path)
    async def add(a, b):
        return a + b

    result = await add(1, 2)

    assert result == 3
    assert os.path.exists(output_path)


@pytest.mark.asyncio
async def test_profiled_writes_output_even_when_wrapped_function_raises(tmp_path):
    output_path = str(tmp_path / "profile.html")

    @profiled(output_path=output_path)
    async def boom():
        raise ValueError("failure")

    with pytest.raises(ValueError, match="failure"):
        await boom()

    assert os.path.exists(output_path)


@pytest.mark.asyncio
async def test_profiled_preserves_function_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    @profiled()
    async def my_function():
        return None

    assert my_function.__name__ == "my_function"
