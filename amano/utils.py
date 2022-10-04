from enum import Enum


class StringEnum(Enum):
    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other

        return other == self
