from pycraftcore.web.enum.web_framework import WebFramework
from pycraftcore.web.port.web_application_factory import WebApplicationFactory


def web_application_factory(framework: WebFramework) -> WebApplicationFactory:
    match framework:
        case WebFramework.FASTAPI:
            from pycraftcore.web_fastapi import FastApiApplicationFactory

            return FastApiApplicationFactory()
        case WebFramework.LITESTAR:
            from pycraftcore.web_litestar import LitestarApplicationFactory

            return LitestarApplicationFactory()
        case WebFramework.BLACKSHEEP:
            from pycraftcore.web_blacksheep import BlackSheepApplicationFactory

            return BlackSheepApplicationFactory()
