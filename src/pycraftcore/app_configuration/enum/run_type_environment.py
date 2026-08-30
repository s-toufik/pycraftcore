from enum import Enum


class RunTypeEnvironment(Enum):
    debug = "debug"
    production = "prod"
    staging = "stg"
    develop = "dev"
