import enum


class AuthType(enum.Enum):
    token = "token"
    basic = "basic"
    none = "none"
