from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class HostBridgeConfig:
    host: str
    port: int
    token: str
    function_names: tuple[str, ...] = field(default=())
