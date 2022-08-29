from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Any

from astroid.decorators import cachedproperty

from .base_attribute import AbstractAttribute, AttributeType, AttributeValue, VALID_TYPE_VALUES, serializer_registry, serialize_value
from .constants import CONDITION_COMPARATOR_EQ, CONDITION_COMPARATOR_NEQ, \
    CONDITION_COMPARATOR_LT, CONDITION_COMPARATOR_LTE, CONDITION_COMPARATOR_GT, \
    CONDITION_COMPARATOR_GTE
from .utils import StringEnum

_COUNTER = 0


def _param_suffix() -> str:
    global _COUNTER
    _COUNTER += 1
    return "_" + "".join(random.choices(string.ascii_letters, k=4)) \
           + str(_COUNTER)


class Condition(ABC):
    values: Dict[str, AttributeValue] = {}

    def __init__(self, **kwargs):
        self.format_params = dict(kwargs)

    @property
    @abstractmethod
    def format(self) -> str:
        ...

    def __str__(self) -> str:
        return self.format.format(**self.format_params)

    def __and__(self, other) -> AndCondition:
        return AndCondition(self, other)

    def __or__(self, other) -> OrCondition:
        return OrCondition(self, other)


class AttributeExists(Condition):
    def __init__(self, attribute: AbstractAttribute):
        super().__init__(attribute=str(attribute))

    @property
    def format(self) -> str:
        return "attribute_exists({attribute})"


class AttributeNotExists(Condition):
    def __init__(self, attribute: AbstractAttribute):
        super().__init__(attribute=str(attribute))

    @property
    def format(self) -> str:
        return "attribute_not_exists({attribute})"


class BeginsWithCondition(Condition):
    def __init__(
        self,
        attribute: AbstractAttribute,
        value: str
    ):
        param_name = f":{attribute}{_param_suffix()}"
        self.values = {
            param_name: {
                "S": str(value)
            }
        }
        super().__init__(attribute=str(attribute), value=param_name)

    @property
    def format(self) -> str:
        return "begins_with({attribute}, {value})"


class ContainsCondition(Condition):
    def __init__(
        self,
        attribute: AbstractAttribute,
        value: Any
    ):
        param_name = f":{attribute}{_param_suffix()}"
        if attribute.type not in (AttributeType.STRING, AttributeType.STRING_SET, AttributeType.NUMBER_SET, AttributeType.BINARY_SET):
            raise ValueError(f"Attribute `{attribute}` does not support `contains` function.")

        if attribute.type is AttributeType.NUMBER_SET:
            value_type = AttributeType.NUMBER
        elif attribute.type is AttributeType.BINARY_SET:
            value_type = AttributeType.BINARY
        else:
            value_type = AttributeType.STRING

        if not isinstance(value, VALID_TYPE_VALUES[str(value_type)]):
            raise ValueError(
                f"Passed value of type `{type(value)}` cannot be used with "
                f"contains function and `{attribute.name}` attribute's type."
            )

        serializer = serializer_registry.get_for(type(value))
        self.values = {
            param_name: serialize_value(serializer.extract(value)),
        }

        super().__init__(attribute=str(attribute), value=param_name)

    @property
    def format(self) -> str:
        return "contains({attribute}, {value})"


class AttributeIsType(Condition):
    def __init__(
        self,
        attribute: AbstractAttribute,
        expected_type: AttributeType
    ):
        param_name = f":{attribute}{_param_suffix()}"
        self.expected_type = expected_type
        self.values = {
            param_name: {
                "S": str(expected_type)
            }
        }
        super().__init__(attribute=str(attribute), expected_type=param_name)

    @property
    def format(self) -> str:
        return "attribute_type({attribute}, {expected_type})"


class LogicalCondition(Condition, ABC):
    def __init__(
        self,
        left_condition: Union[Condition, str],
        right_condition: Union[Condition, str]
    ):
        super().__init__(
            left_condition=left_condition,
            right_condition=right_condition
        )
        self.left_condition = left_condition
        self.right_condition = right_condition

    @cachedproperty
    def values(self) -> Dict[str, AttributeValue]:
        values = {}
        if hasattr(self.left_condition, "values"):
            values = self.left_condition.values

        if hasattr(self.right_condition, "values"):
            values = {**values, **self.right_condition.values}

        return values


class AndCondition(LogicalCondition):
    @property
    def format(self) -> str:
        return "({left_condition} AND {right_condition})"


class OrCondition(LogicalCondition):
    @property
    def format(self) -> str:
        return "({left_condition} OR {right_condition})"


class NotCondition(Condition):
    def __init__(self, condition: Union[Condition, str]):
        super().__init__(condition)

    @property
    def format(self) -> str:
        return "(NOT {0})"


class ComparisonCondition(Condition):

    class ComparisonOperator(StringEnum):
        EQ = CONDITION_COMPARATOR_EQ
        NEQ = CONDITION_COMPARATOR_NEQ
        LT = CONDITION_COMPARATOR_LT
        LTE = CONDITION_COMPARATOR_LTE
        GT = CONDITION_COMPARATOR_GT
        GTE = CONDITION_COMPARATOR_GTE

    def __init__(
        self,
        operator: ComparisonOperator,
        left_operand: AbstractAttribute,
        right_operand: Any
    ):
        self.values = {}
        if isinstance(right_operand, AbstractAttribute):
            super().__init__(
                operator=operator,
                left_operand=left_operand,
                right_operand=right_operand
            )
            return

        if isinstance(right_operand, Condition):
            raise ValueError(f"Could not compare `{left_operand}` with a condition expression.")

        # validate value type
        AttributeType.from_python_type(type(right_operand))
        param_name = f":{left_operand}{_param_suffix()}"
        self.values = {param_name: left_operand.extract(right_operand)}
        super().__init__(
            operator=operator,
            left_operand=left_operand,
            right_operand=param_name
        )

    @property
    def format(self) -> str:
        return "{left_operand} {operator} {right_operand}"


class SizeCondition(Condition):
    def __init__(self, attribute: AbstractAttribute):
        super().__init__(attribute=attribute.name)
        self.values = {}

    @property
    def format(self) -> str:
        if "operator" not in self.format_params:
            return "size({attribute})"

        return "size({attribute}) {operator} {value}"

    def __eq__(self, value: int) -> SizeCondition:
        return self._compare_size(CONDITION_COMPARATOR_EQ, value)

    def __gt__(self, value: int) -> SizeCondition:
        return self._compare_size(CONDITION_COMPARATOR_GT, value)

    def __ge__(self, value: int) -> SizeCondition:
        return self._compare_size(CONDITION_COMPARATOR_GTE, value)

    def __lt__(self, value: int) -> SizeCondition:
        return self._compare_size(CONDITION_COMPARATOR_LT, value)

    def __le__(self, value: int) -> SizeCondition:
        return self._compare_size(CONDITION_COMPARATOR_LTE, value)

    def _compare_size(self, operator: str, value: int) -> SizeCondition:
        param_name = f":{self.format_params['attribute']}_size{_param_suffix()}"
        self.format_params["operator"] = operator
        self.format_params["value"] = param_name
        self.values[param_name] = {
            "N": str(value),
        }
        return self
