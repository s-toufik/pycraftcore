from enum import Enum


class FileOperationAction(Enum):
    read = "read"
    write = "write"
    delete = "delete"
