from typing import Set

import pytest

from amano.attribute import Attribute
from amano.base_attribute import AttributeType
from amano.condition import ComparisonCondition


@pytest.mark.usefixtures("generic_field_identifier")
def test_comparison_condition_with_const_value() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field == 12

    # then
    assert isinstance(condition, ComparisonCondition)
    assert str(condition) == "field = :field"
    assert condition.values[":field"] == {"N": "12"}
    assert condition.attributes == {"field"}


def test_comparison_condition_with_two_attributes() -> None:
    # given
    field = Attribute("field", int)
    other_field = Attribute("other_field", int)

    # when
    condition = field == other_field

    # then
    assert str(condition) == "field = other_field"
    assert not condition.values
    assert condition.attributes == {"field", "other_field"}


@pytest.mark.usefixtures("generic_field_identifier")
def test_comparison_with_and_expression() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = (field > 12) & (field < 20)

    # then
    assert str(condition) == "(field > :field AND field < :field)"
    assert condition.left_condition.values == {":field": {"N": "12"}}
    assert condition.right_condition.values == {":field": {"N": "20"}}


@pytest.mark.usefixtures("generic_field_identifier")
def test_comparison_with_or_expression() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = (field > 12) | (field < 20)

    # then
    assert str(condition) == "(field > :field OR field < :field)"
    assert condition.left_condition.values == {":field": {"N": "12"}}
    assert condition.right_condition.values == {":field": {"N": "20"}}


@pytest.mark.usefixtures("generic_field_identifier")
def test_comparison_with_complex_expression() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = ((field > 12) & (field < 20)) | ((field == 12) | (field == 13))

    # then
    assert (
        str(condition)
        == "((field > :field AND field < :field) OR (field = :field OR field = :field))"
    )


def test_attribute_exists_function() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field.exists()

    # then
    assert str(condition) == "attribute_exists(field)"


def test_attribute_not_exists_function() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field.not_exists()

    # then
    assert str(condition) == "attribute_not_exists(field)"


@pytest.mark.usefixtures("generic_field_identifier")
def test_attribute_type_function() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field.is_type(AttributeType.STRING)

    # then
    assert str(condition) == "attribute_type(field, :field)"
    assert condition.values[":field"] == {"S": "S"}


@pytest.mark.usefixtures("generic_field_identifier")
def test_begins_with_function() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field.begins_with("test")

    # then
    assert str(condition) == "begins_with(field, :field)"
    assert condition.values[":field"] == {"S": "test"}


@pytest.mark.usefixtures("generic_field_identifier")
def test_contains_function() -> None:
    # given
    field = Attribute("field", Set[int])

    # when
    condition = field.contains(12)

    # then
    assert str(condition) == "contains(field, :field)"
    assert condition.values[":field"] == {"N": "12"}


@pytest.mark.usefixtures("generic_field_identifier")
def test_size_function_with_comparison() -> None:
    # given
    field = Attribute("field", Set[int])

    # when
    condition = field.size() > 11

    # then
    assert str(condition) == "size(field) > :field_size"
    assert condition.values[":field_size"] == {"N": "11"}


def test_size_function() -> None:
    # given
    field = Attribute("field", Set[int])

    # when
    condition = field.size()

    # then
    assert str(condition) == "size(field)"


@pytest.mark.usefixtures("generic_field_identifier")
def test_between_function() -> None:
    # given
    field = Attribute("field", str)

    # when
    condition = field.between("a", "z")

    # then
    assert str(condition) == "field BETWEEN :field_a AND :field_b"
    assert condition.values[":field_a"] == {"S": "a"}
    assert condition.values[":field_b"] == {"S": "z"}
