from dataclasses import dataclass, field


@dataclass(slots=True)
class SecuritySettings:
    certificate: str | None = field(default=None)
    tls_cipher_spec: str | None = field(default=None)
