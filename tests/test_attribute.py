import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from numbers import Integral
from typing import (
    AnyStr,
    Callable,
    Dict,
    FrozenSet,
    Generic,
    List,
    Set,
    TextIO,
    Tuple,
    TypedDict,
)

import pytest

from amano.attribute import Attribute, AttributeType


def test_can_instantiate() -> None:
    # given
    instance = Attribute[str]("name")

    # then
    assert isinstance(instance, Attribute)
    assert instance.name == "name"
    assert instance.type == AttributeType.STRING


@dataclass
class ExampleDataClass:
    field_a: str
    field_b: str


class ExampleTypedDict(TypedDict):
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
        [ExampleTypedDict, AttributeType.MAP],
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
def test_supported_from_python_type(
    given_type: type, expected_type: AttributeType
) -> None:
    # given
    resolved_attribute = AttributeType.from_python_type(given_type)

    # then
    assert resolved_attribute == expected_type

    # given
    attribute = Attribute[given_type]("test")

    # then
    assert isinstance(attribute, Attribute)


def test_can_attribute_use_typed_dict() -> None:
    class Point(TypedDict):
        x: int
        y: int

    attribute = Attribute[Point]("test")

    assert attribute.type == AttributeType.MAP


def test_float_attribute() -> None:
    # given
    attribute = Attribute[float]("test")

    # when
    extracted_value = attribute.extract(10.4213)

    # then
    assert extracted_value == Decimal("10.4213")

    # when
    hydrated_value = attribute.hydrate("10.4213")

    # then
    assert isinstance(hydrated_value, float)
    assert hydrated_value == 10.4213


def test_attribute_path() -> None:
    # given
    test = Attribute[float]("test")

    # then
    assert test.key("sub.field").name == "test.sub.field"


def test_can_extract_any_attribute_path() -> None:
    # given
    test = Attribute[float]("test")

    # then
    assert re.match(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}",
        test.key("sub.field").extract(datetime.now())
    )

    assert test.key("sub.field").extract(10) == 10
    assert test.key("sub.field").extract(10.4) == Decimal("10.4")
