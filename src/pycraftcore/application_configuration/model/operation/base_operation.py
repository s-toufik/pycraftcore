from dataclasses import dataclass

from pycraftcore.application_configuration.enum.operation_type import OperationType


@dataclass(slots=True)
class BaseOperation:
    name: str
    type: OperationType
