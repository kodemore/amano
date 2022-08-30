from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from numbers import Integral
from typing import AnyStr, Callable, Dict, FrozenSet, Generic, List, Set, TextIO, Tuple, TypedDict

import pytest

from amano.attribute import Attribute, AttributeType


def test_can_instantiate() -> None:
    # given
    instance = Attribute("name", str)

    # then
    assert isinstance(instance, Attribute)
    assert instance.name == "name"
    assert instance.type == AttributeType.STRING


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
        AttributeType.from_python_type(given_type)


@pytest.mark.parametrize(
    "given_type,expected_type",
    [
        [str, AttributeType.STRING],
        [AnyStr, AttributeType.STRING],
        [datetime, AttributeType.STRING],
        [date, AttributeType.STRING],
        [time, AttributeType.STRING],
        [Decimal, AttributeType.NUMBER],
        [int, AttributeType.NUMBER],
        [float, AttributeType.NUMBER],
        [list, AttributeType.LIST],
        [List, AttributeType.LIST],
        [Tuple, AttributeType.LIST],
        [tuple, AttributeType.LIST],
        [Set, AttributeType.LIST],
        [set, AttributeType.LIST],
        [FrozenSet, AttributeType.LIST],
        [frozenset, AttributeType.LIST],
        [dict, AttributeType.MAP],
        [Dict, AttributeType.MAP],
        [ExampleDataClass, AttributeType.MAP],
        [TypedDict, AttributeType.MAP],
        [bool, AttributeType.BOOLEAN],
        [bytes, AttributeType.BINARY],
        [bytearray, AttributeType.BINARY],
        [Set[str], AttributeType.STRING_SET],
        [Set[date], AttributeType.STRING_SET],
        [Set[datetime], AttributeType.STRING_SET],
        [Set[time], AttributeType.STRING_SET],
        [FrozenSet[str], AttributeType.STRING_SET],
        [Set[Decimal], AttributeType.NUMBER_SET],
        [Set[int], AttributeType.NUMBER_SET],
        [Set[float], AttributeType.NUMBER_SET],
        [Set[bytes], AttributeType.BINARY_SET],
        [Set[bytearray], AttributeType.BINARY_SET],
    ],
)
def test_supported_from_python_type(given_type: type, expected_type: AttributeType) -> None:
    # given
    resolved_attribute = AttributeType.from_python_type(given_type)

    # then
    assert resolved_attribute == expected_type


def test_float_attribute() -> None:
    # given
    attribute = Attribute("test", float)

    # when
    extracted_value = attribute.extract(10.4213)

    # then
    assert extracted_value == {"N": "10.4213"}

    # when
    hydrated_value = attribute.hydrate({"N": "10.4213"})

    # then
    assert isinstance(hydrated_value, float)
    assert hydrated_value == 10.4213
