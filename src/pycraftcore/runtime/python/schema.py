from dataclasses import dataclass

from pydantic import BaseModel, Field


class SafeCodeSettings(BaseModel):
    code_timeout: int | None = Field(default=10)
    max_memory_mb: int | None = Field(default=256)


@dataclass
class CodeStdout:
    stdout: str
    stderr: str
