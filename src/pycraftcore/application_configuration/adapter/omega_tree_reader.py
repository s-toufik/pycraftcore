from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from omegaconf import DictConfig, OmegaConf

FILE_EXTENSION: str = "yml"


class OmegaTreeReader:
    def __init__(self, root_file: Path, folders: Sequence[Path] = ()) -> None:
        self._root_file = root_file
        self._folders = tuple(folders)

    def read(self, key: str) -> dict[str, Any]:
        tree: DictConfig = self._merged()
        if key not in tree:
            raise KeyError(f"{self._root_file} has no {key!r} section")
        section: Any = tree[key]
        if not isinstance(section, DictConfig):
            raise ValueError(f"{key!r} in {self._root_file} must be a mapping")
        container: Any = OmegaConf.to_container(section, resolve=True, throw_on_missing=True)
        return cast(dict[str, Any], container)

    def _merged(self) -> DictConfig:
        if not self._root_file.is_file():
            raise FileNotFoundError(f"No root file at {self._root_file}")
        return cast(
            DictConfig,
            OmegaConf.merge(
                *(
                    OmegaConf.load(file)
                    for folder in self._folders
                    for file in sorted(folder.glob(f"*.{FILE_EXTENSION}"))
                ),
                OmegaConf.load(self._root_file),
            ),
        )
