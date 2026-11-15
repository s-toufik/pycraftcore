from pydantic import BaseModel


class SqliteConnector(BaseModel):
    path: str
    database: str
    max_pool_size: int
