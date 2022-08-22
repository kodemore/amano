from __future__ import annotations

import enum
from datetime import datetime, date, time
from decimal import Decimal
from typing import overload, List, Set, FrozenSet, Dict, TypedDict, Tuple, AnyStr, Any

from chili import is_dataclass, HydrationStrategy
from chili.hydration import StrategyRegistry
from chili.typing import get_origin_type, get_type_args


class FloatStrategy(HydrationStrategy):
    def hydrate(self, value: Any) -> float:
        return float(value)

    def extract(self, value: Any) -> Decimal:  # decimal is understood by dynamodb
        return Decimal(str(value))


_serializer_registry = StrategyRegistry()

# Add support for floats in dynamodb
_serializer_registry.add(float, FloatStrategy())


_SUPPORTED_BASE_TYPES = {
    str: "S",
    AnyStr: "S",
    datetime: "S",
    date: "S",
    time: "S",
    Decimal: "S",
    int: "N",
    float: "N",
    list: "L",
    List: "L",
    set: "L",
    Set: "L",
    frozenset: "L",
    FrozenSet: "L",
    tuple: "L",
    Tuple: "L",
    dict: "M",
    Dict: "M",
    TypedDict: "M",
    type(None): "NULL",
    bytes: "B",
    bytearray: "B",
    bool: "BOOL",
}

_SUPPORTED_GENERIC_TYPES = {
    list: "L",
    tuple: "L",
    set: "L",
    frozenset: "L",
    dict: "M",
}


class Attribute:
    class Type(enum.Enum):
        STRING = "S"
        NUMBER = "N"
        BOOLEAN = "BOOL"
        BINARY = "B"
        NULL = "NULL"
        LIST = "L"
        MAP = "M"
        NUMBER_SET = "NS"
        STRING_SET = "SS"
        BINARY_SET = "BS"

        @classmethod
        def from_python_type(cls, value_type: type) -> Attribute.Type:
            if value_type in _SUPPORTED_BASE_TYPES.keys():
                return Attribute.Type(_SUPPORTED_BASE_TYPES[value_type])

            if is_dataclass(value_type):
                return Attribute.Type.MAP

            origin_type = get_origin_type(value_type)

            if origin_type not in _SUPPORTED_GENERIC_TYPES:
                raise TypeError(f"Unsupported type {value_type}")

            if origin_type is set or origin_type is frozenset:
                value_subtype = get_type_args(value_type)[0]
                mapped_type = cls.from_python_type(value_subtype)

                if mapped_type == Attribute.Type.STRING:
                    return Attribute.Type.STRING_SET

                if mapped_type == Attribute.Type.NUMBER:
                    return Attribute.Type.NUMBER_SET

                if mapped_type == Attribute.Type.BINARY:
                    return Attribute.Type.BINARY_SET

            return Attribute.Type(_SUPPORTED_GENERIC_TYPES[origin_type])

        @overload
        def __eq__(self, other: str) -> bool:
            ...

        @overload
        def __eq__(self, other: Attribute.Type) -> bool:
            ...

        def __eq__(self, other):
            if isinstance(other, str):
                return self.value == other

            if isinstance(other, Attribute.Type):
                return self.value == other.value

            raise TypeError(f"Comparison between {self.__class__} and {type(other)} is not supported.")

    def __init__(self, name: str, attribute_type: type, default_value: Any = None):
        self.name = name
        self.type = Attribute.Type.from_python_type(attribute_type)
        self.strategy = _serializer_registry.get_for(attribute_type, strict=True)
        self.default_value = default_value

    def extract(self, value: Any) -> Any:
        return self.strategy.extract(value)

    def hydrate(self, value: Any) -> Any:
        return self.strategy.hydrate(value)
