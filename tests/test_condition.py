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
