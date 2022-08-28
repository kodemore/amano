from amano.attribute import Attribute
from amano.condition import ComparisonCondition


def test_comparison_condition_with_const_value() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field == 12

    # then
    assert isinstance(condition, ComparisonCondition)
    assert str(condition) == "field = :field"
    assert condition.values[":field"] == {"N": "12"}


def test_comparison_condition_with_two_attributes() -> None:
    # given
    field = Attribute("field", int)
    other_field = Attribute("other_field", int)

    # when
    condition = field == other_field

    # then
    assert str(condition) == "field = other_field"
    assert not condition.values


def test_comparison_with_and_expression(field_identifier: str) -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = (field > 12) & (field < 20)

    # then
    assert str(condition) == "(field > :field AND field < :field)"
    assert condition.left_condition.values == {":field": {"N": "12"}}
    assert condition.right_condition.values == {":field": {"N": "20"}}


def test_comparison_with_or_expression(field_identifier: str) -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = (field > 12) | (field < 20)

    # then
    assert str(condition) == "(field > :field OR field < :field)"
    assert condition.left_condition.values == {":field": {"N": "12"}}
    assert condition.right_condition.values == {":field": {"N": "20"}}


def test_comparison_with_complex_expression(field_identifier: str) -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = ((field > 12) & (field < 20)) | ((field == 12) | (field == 13))

    # then
    assert str(condition) == "((field > :field AND field < :field) OR (field = :field OR field = :field))"
