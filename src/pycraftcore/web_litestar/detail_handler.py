from collections.abc import Callable

from litestar import Request, Response


def detail_handler(status_code: int) -> Callable[[Request, Exception], Response]:
    def handle(_request: Request, exception: Exception) -> Response:
        return Response({"detail": str(exception)}, status_code=status_code)

    return handle
