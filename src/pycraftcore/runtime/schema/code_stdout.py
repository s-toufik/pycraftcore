from dataclasses import dataclass


@dataclass
class CodeStdout:
    stdout: str
    stderr: str
