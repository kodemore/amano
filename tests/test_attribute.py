from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from numbers import Integral
from typing import AnyStr, Callable, Dict, FrozenSet, Generic, List, Set, TextIO, Tuple, TypedDict

import pytest

from amano import Attribute


def test_can_instantiate() -> None:
    # given
    instance = Attribute("name", str)

    # then
    assert isinstance(instance, Attribute)
    assert instance.name == "name"
    assert instance.type == Attribute.Type.STRING


@dataclass
class ExampleDataClass:
    field_a: str
    field_b: str


@pytest.mark.parametrize(
    "given_type",
    [
        Integral,
        Callable,
        Generic,
        TextIO,
    ],
)
def test_unsupported_from_python_type(given_type: type) -> None:
    # then
    with pytest.raises(TypeError):
        Attribute.Type.from_python_type(given_type)


@pytest.mark.parametrize(
    "given_type,expected_type",
    [
        [str, Attribute.Type.STRING],
        [AnyStr, Attribute.Type.STRING],
        [datetime, Attribute.Type.STRING],
        [date, Attribute.Type.STRING],
        [time, Attribute.Type.STRING],
        [Decimal, Attribute.Type.NUMBER],
        [int, Attribute.Type.NUMBER],
        [float, Attribute.Type.NUMBER],
        [list, Attribute.Type.LIST],
        [List, Attribute.Type.LIST],
        [Tuple, Attribute.Type.LIST],
        [tuple, Attribute.Type.LIST],
        [Set, Attribute.Type.LIST],
        [set, Attribute.Type.LIST],
        [FrozenSet, Attribute.Type.LIST],
        [frozenset, Attribute.Type.LIST],
        [dict, Attribute.Type.MAP],
        [Dict, Attribute.Type.MAP],
        [ExampleDataClass, Attribute.Type.MAP],
        [TypedDict, Attribute.Type.MAP],
        [bool, Attribute.Type.BOOLEAN],
        [bytes, Attribute.Type.BINARY],
        [bytearray, Attribute.Type.BINARY],
        [Set[str], Attribute.Type.STRING_SET],
        [Set[date], Attribute.Type.STRING_SET],
        [Set[datetime], Attribute.Type.STRING_SET],
        [Set[time], Attribute.Type.STRING_SET],
        [FrozenSet[str], Attribute.Type.STRING_SET],
        [Set[Decimal], Attribute.Type.NUMBER_SET],
        [Set[int], Attribute.Type.NUMBER_SET],
        [Set[float], Attribute.Type.NUMBER_SET],
        [Set[bytes], Attribute.Type.BINARY_SET],
        [Set[bytearray], Attribute.Type.BINARY_SET],
    ],
)
def test_supported_from_python_type(given_type: type, expected_type: Attribute.Type) -> None:
    # given
    resolved_attribute = Attribute.Type.from_python_type(given_type)

    # then
    assert resolved_attribute == expected_type


def test_float_attribute() -> None:
    # given
    attribute = Attribute("test", float)

    # when
    extracted_value = attribute.extract(10.4213)

    # then
    assert isinstance(extracted_value, Decimal)
    assert extracted_value == Decimal("10.4213")

    # when
    hydrated_value = attribute.hydrate(Decimal("10.4213"))

    # then
    assert hydrated_value == 10.4213
