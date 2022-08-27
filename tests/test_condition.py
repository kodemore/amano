from amano.condition import ComparisonCondition
from amano.attribute import Attribute


def test_comparison_condition() -> None:
    # given
    field = Attribute("field", int)
    condition = field == 12

    # then
    assert isinstance(condition, ComparisonCondition)
    assert str(condition) == "field = :field"
