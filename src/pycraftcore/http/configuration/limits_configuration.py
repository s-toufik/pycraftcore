from dataclasses import dataclass, field


@dataclass(slots=True)
class LimitsSettings:
    timeout: int = field(default=30)
    keep_alive_timeout: int = field(default=60)
    ttl_dns_cache: int = field(default=600)
    max_connections: int = field(default=1000)
    max_connections_per_host: int = field(default=100)
    max_keepalive_connections: int = field(default=50)
