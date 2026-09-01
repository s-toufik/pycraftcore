import asyncio
import functools
from pathlib import Path

from pyinstrument import Profiler


def profiled(output_path: str = "profile.html"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            profiler = Profiler(async_mode="enabled")
            profiler.start()
            try:
                return await func(*args, **kwargs)
            finally:
                profiler.stop()
                await asyncio.to_thread(
                    Path(output_path).write_text,
                    profiler.output_html(),
                    encoding="utf-8",
                )

        return wrapper

    return decorator
