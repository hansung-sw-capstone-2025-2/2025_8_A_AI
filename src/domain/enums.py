from enum import Enum


class SearchMode(str, Enum):
    STRICT = "strict"
    FLEXIBLE = "flexible"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
