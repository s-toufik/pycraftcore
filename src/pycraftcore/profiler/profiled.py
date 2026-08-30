import functools
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
                with open(output_path, "w") as f:
                    f.write(profiler.output_html())

        return wrapper

    return decorator
