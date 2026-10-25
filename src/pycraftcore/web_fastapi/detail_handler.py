from fastapi import Request
from fastapi.responses import JSONResponse, Response

from pycraftcore.web_fastapi.app_factory import ExceptionHandler


def detail_handler(status_code: int) -> ExceptionHandler:
    async def handle(_request: Request, exception: Exception) -> Response:
        return JSONResponse({"detail": str(exception)}, status_code=status_code)

    return handle
