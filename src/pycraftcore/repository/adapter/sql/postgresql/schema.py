from pydantic import BaseModel


class PostgresConnector(BaseModel):
    host: str
    port: int
    default_name: str
    user: str | None
    password: str | None
    min_pool_size: int
    max_pool_size: int
