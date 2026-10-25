from blacksheep import Application, Request, Response, json

from pycraftcore.web_blacksheep.app_factory import ExceptionHandler


def detail_handler(status_code: int) -> ExceptionHandler:
    async def handle(_app: Application, _request: Request, exception: Exception) -> Response:
        return json({"detail": str(exception)}, status=status_code)

    return handle
