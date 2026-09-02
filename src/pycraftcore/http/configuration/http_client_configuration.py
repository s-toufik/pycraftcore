from dataclasses import dataclass, field

from pycraftcore.http.configuration.client_configuration import ClientSettings
from pycraftcore.http.configuration.limits_configuration import LimitsSettings
from pycraftcore.http.configuration.security_configuration import SecuritySettings


@dataclass(slots=True)
class HttpClientSettings:
    client_params: ClientSettings = field(default_factory=ClientSettings)
    limits: LimitsSettings = field(default_factory=LimitsSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
