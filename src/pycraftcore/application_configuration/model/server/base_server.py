from dataclasses import dataclass

from pycraftcore.application_configuration.enum.server_type import ServerType


@dataclass(slots=True)
class BaseServer:
    name: str
    type: ServerType
