from typing import Protocol

from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema.web_application import WebApplication


class WebApplicationFactory(Protocol):
    def create(self, application: WebApplication) -> ASGIApp: ...
