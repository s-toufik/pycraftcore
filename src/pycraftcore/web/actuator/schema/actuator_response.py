from pydantic import BaseModel

from pycraftcore.web.actuator.enum.health_status import HealthStatus


class HealthSchema(BaseModel):
    status: HealthStatus


class InfoSchema(BaseModel):
    name: str
    version: str
    environment: str
    authors: str
