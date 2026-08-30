from dataclasses import dataclass, field


@dataclass(slots=True)
class ClientSettings:
    base_url: str = field(default="")