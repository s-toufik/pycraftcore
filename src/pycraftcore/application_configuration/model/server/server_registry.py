from collections.abc import Mapping
from dataclasses import dataclass, field

from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model.server.asgi_server import AsgiServer


@dataclass(frozen=True, slots=True)
class ServerRegistry:
    by_type: dict[ServerType, dict[str, AsgiServer]] = field(default_factory=dict)

    def __getitem__(self, kind: ServerType) -> Mapping[str, AsgiServer]:
        return self.by_type.get(kind, {})

    def asgi(self, name: str) -> AsgiServer:
        try:
            return self.by_type[ServerType.asgi][name]
        except KeyError:
            raise KeyError(f"no asgi server named {name!r}") from None
