from dataclasses import dataclass
from pathlib import Path

DATABASE_SUFFIX: str = ".db"


@dataclass(frozen=True, slots=True)
class SqliteDatabaseFile:
    directory: str
    name: str

    @property
    def path(self) -> Path:
        return Path(self.directory) / f"{self.name}{DATABASE_SUFFIX}"

    def prepare(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return self.path
