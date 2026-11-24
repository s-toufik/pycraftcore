from dataclasses import dataclass

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.authentication import AuthTyping


@dataclass(slots=True)
class BaseConnector:
    name: str
    type: ConnectorType
    auth: AuthTyping
