from enum import StrEnum


class SystemRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class TeamRole(StrEnum):
    MEMBER = "member"
    PM = "pm"
    TL = "tl"
    