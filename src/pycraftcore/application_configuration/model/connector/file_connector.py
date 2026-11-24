from dataclasses import dataclass

from pycraftcore.application_configuration.model.connector.base_connector import BaseConnector


@dataclass(slots=True)
class FileConnector(BaseConnector):
    base_path: str
