from dataclasses import dataclass, field

from pycraftcore.application_configuration.model.connector.base_connector import BaseConnector


@dataclass(slots=True)
class ApiConnector(BaseConnector):
    base_url: str
    timeout: int
    retry: int
    certificate: str | None = field(default=None)
