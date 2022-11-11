from __future__ import annotations

from abc import ABC, abstractmethod
from functools import reduce
from typing import final


class AttributeMappingStrategy(ABC):
    @abstractmethod
    def __getitem__(self, item: str) -> str:
        ...

    def __contains__(self, item: str) -> bool:
        return True


class PassThroughAttributeMapping(AttributeMappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item

    def __contains__(self, item) -> bool:
        return False


class HyphensAttributeMapping(AttributeMappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item.replace("_", "-")


class PascalCaseAttributeMapping(AttributeMappingStrategy):
    def __getitem__(self, item: str) -> str:
        def upper_first(val: str) -> str:
            if len(val) > 1:
                return val[0].upper() + val[1:]
            return val.upper()

        camel_case = reduce(lambda x, y: x + upper_first(y), item.split("_"))
        if len(camel_case) > 1:
            return camel_case[0].upper() + camel_case[1:]
        return camel_case.upper()


class CamelCaseAttributeMapping(AttributeMappingStrategy):
    def __getitem__(self, item: str) -> str:
        return reduce(lambda x, y: x + y.capitalize(), item.split("_"))


@final
class AttributeMapping:
    PASS_THROUGH = PassThroughAttributeMapping()
    PASCAL_CASE = PascalCaseAttributeMapping()
    CAMEL_CASE = CamelCaseAttributeMapping()
    HYPHENS = HyphensAttributeMapping()
