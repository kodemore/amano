import re

from amano.condition import ComparisonCondition
from amano.attribute import Attribute


def test_comparison_condition_with_const_value() -> None:
    # given
    field = Attribute("field", int)

    # when
    condition = field == 12

    # then
    assert isinstance(condition, ComparisonCondition)
    assert str(condition)[:-6] == "field = :field"
    value = list(condition.values.items())[0]
    assert value[0][:-6] == ":field"
    assert value[1] == {"N": "12"}


def test_comparison_condition_with_two_attributes() -> None:
    # given
    field = Attribute("field", int)
    other_field = Attribute("other_field", int)

    # when
    condition = field == other_field

    # then
    assert str(condition) == "field = other_field"


def test_comparison_with_and_expression(field_identifier: str) -> None:
    field = Attribute("field", int)

    # when
    condition = (field > 12) & (field < 20)

    # then
    assert re.match(
        f"^\\(field > :field{field_identifier} AND "
        f"field < :field{field_identifier}\\)$",
        str(condition)
    )


def test_comparison_with_or_expression(field_identifier: str) -> None:
    field = Attribute("field", int)

    # when
    condition = (field > 12) | (field < 20)

    # then
    assert re.match(
        f"^\\(field > :field{field_identifier} OR "
        f"field < :field{field_identifier}\\)$",
        str(condition)
    )
