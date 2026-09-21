from pydantic import BaseModel, Field


class MongoConnector(BaseModel):
    host: str
    port: int
    default_name: str
    username: str | None
    password: str | None = Field(repr=False)
    server_selection_timeout: int
