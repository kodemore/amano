from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce


class MappingStrategy(ABC):
    @abstractmethod
    def __getitem__(self, item: str) -> str:
        ...

    def __contains__(self, item: str) -> bool:
        return True


class PassThroughMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item

    def __contains__(self, item) -> bool:
        return False


class HyphensMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item.replace("_", "-")


class PascalCaseMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        def upper_first(val: str) -> str:
            if len(val) > 1:
                return val[0].upper() + val[1:]
            return val.upper()

        camel_case = reduce(lambda x, y: x + upper_first(y), item.split("_"))
        if len(camel_case) > 1:
            return camel_case[0].upper() + camel_case[1:]
        return camel_case.upper()


class CamelCaseMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return reduce(lambda x, y: x + y.capitalize(), item.split("_"))


class Mapping(Enum):
    PASS_THROUGH = PassThroughMapping()
    PASCAL_CASE = PascalCaseMapping()
    CAMEL_CASE = CamelCaseMapping()
    HYPHENS = HyphensMapping()

    def __getitem__(self, item: str) -> str:
        return self.value[item]

    def __contains__(self, item) -> bool:
        return item in self.value
