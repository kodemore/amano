from enum import Enum


class StringEnum(Enum):
    def __str__(self) -> str:
        return str(self.value)
