from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class SafeCodeSettings(BaseModel):
    code_timeout: Optional[int] = Field(default=10)
    max_memory_mb: Optional[int] = Field(default=256)

@dataclass
class CodeStdout:
    stdout: str
    stderr: str