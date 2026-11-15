from pydantic import BaseModel, Field


class PostgresConnector(BaseModel):
    host: str
    port: int
    database: str
    user: str | None
    password: str | None = Field(repr=False)
    connect_timeout: int
    min_pool_size: int
    max_pool_size: int
