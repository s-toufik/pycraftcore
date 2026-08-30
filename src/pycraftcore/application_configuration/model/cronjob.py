from dataclasses import dataclass

from pycraftcore.application_configuration.model.operation import OperationTyping


@dataclass(slots=True)
class CronJob:
    name: str
    cron: str
    operation: OperationTyping
