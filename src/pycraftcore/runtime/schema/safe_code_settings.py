from pydantic import BaseModel, Field


class SafeCodeSettings(BaseModel):
    code_timeout: int | None = Field(default=10)
    max_memory_mb: int | None = Field(default=256)
    vault_path: str | None = Field(default=None)
