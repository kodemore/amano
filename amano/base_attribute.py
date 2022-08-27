from __future__ import annotations

import enum
from abc import abstractmethod, ABC
from datetime import date, datetime, time
from decimal import Decimal
from typing import AnyStr, Dict, FrozenSet, List, Set, Tuple, TypedDict, overload, Any

from chili import is_dataclass
from chili.typing import get_origin_type, get_type_args
from chili import HydrationStrategy

from constants import (
    TYPE_MAP, TYPE_STRING, TYPE_LIST, TYPE_NULL, TYPE_BINARY,
    TYPE_BINARY_SET, TYPE_NUMBER_SET, TYPE_BOOLEAN, TYPE_NUMBER,
    TYPE_STRING_SET
)


_SUPPORTED_BASE_TYPES = {
    str: TYPE_STRING,
    AnyStr: TYPE_STRING,
    datetime: TYPE_STRING,
    date: TYPE_STRING,
    time: TYPE_STRING,
    Decimal: TYPE_NUMBER,
    int: TYPE_NUMBER,
    float: TYPE_NUMBER,
    list: TYPE_LIST,
    List: TYPE_LIST,
    set: TYPE_LIST,
    Set: TYPE_LIST,
    frozenset: TYPE_LIST,
    FrozenSet: TYPE_LIST,
    tuple: TYPE_LIST,
    Tuple: TYPE_LIST,
    dict: TYPE_MAP,
    Dict: TYPE_MAP,
    TypedDict: TYPE_MAP,
    type(None): TYPE_NULL,
    bytes: TYPE_BINARY,
    bytearray: TYPE_BINARY,
    bool: TYPE_BOOLEAN,
}

_SUPPORTED_GENERIC_TYPES = {
    list: TYPE_LIST,
    tuple: TYPE_LIST,
    set: TYPE_LIST,
    frozenset: TYPE_LIST,
    dict: TYPE_MAP,
}


class AttributeType(enum.Enum):
    STRING = TYPE_STRING
    NUMBER = TYPE_NUMBER
    BOOLEAN = TYPE_BOOLEAN
    BINARY = TYPE_BINARY
    NULL = TYPE_NULL
    LIST = TYPE_LIST
    MAP = TYPE_MAP
    NUMBER_SET = TYPE_NUMBER_SET
    STRING_SET = TYPE_STRING_SET
    BINARY_SET = TYPE_BINARY_SET

    @classmethod
    def from_python_type(cls, value_type: type) -> AttributeType:
        if value_type in _SUPPORTED_BASE_TYPES.keys():
            return AttributeType(_SUPPORTED_BASE_TYPES[value_type])

        if is_dataclass(value_type):
            return AttributeType.MAP

        origin_type = get_origin_type(value_type)

        if origin_type not in _SUPPORTED_GENERIC_TYPES:
            raise TypeError(f"Unsupported type {value_type}")

        if origin_type is set or origin_type is frozenset:
            value_subtype = get_type_args(value_type)[0]
            mapped_type = cls.from_python_type(value_subtype)

            if mapped_type == AttributeType.STRING:
                return AttributeType.STRING_SET

            if mapped_type == AttributeType.NUMBER:
                return AttributeType.NUMBER_SET

            if mapped_type == AttributeType.BINARY:
                return AttributeType.BINARY_SET

        return AttributeType(_SUPPORTED_GENERIC_TYPES[origin_type])

    @overload
    def __eq__(self, other: str) -> bool:
        ...

    @overload
    def __eq__(self, other: AttributeType) -> bool:
        ...

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other

        if isinstance(other, AttributeType):
            return self.value == other.value

        raise TypeError(f"Comparison between {self.__class__} and {type(other)} is not supported.")


class AbstractAttribute(ABC):
    name: str
    type: AttributeType
    default_value: Any
    strategy: HydrationStrategy

    @abstractmethod
    def extract(self, value: Any) -> Any:
        ...

    def hydrate(self, value: Any) -> Any:
        ...
