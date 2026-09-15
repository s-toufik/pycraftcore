from dataclasses import dataclass


@dataclass(slots=True)
class FileManifest:
    file_path: str
    byte_size: int
    line_count: int
