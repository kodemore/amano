from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from typing import Any, Dict, Set, Union

from astroid.decorators import cachedproperty

from .base_attribute import (
    VALID_TYPE_VALUES,
    AbstractAttribute,
    AttributeType,
    AttributeValue,
    serialize_value,
    serializer_registry,
)
from .constants import (
    CONDITION_COMPARATOR_EQ,
    CONDITION_COMPARATOR_GT,
    CONDITION_COMPARATOR_GTE,
    CONDITION_COMPARATOR_LT,
    CONDITION_COMPARATOR_LTE,
    CONDITION_COMPARATOR_NEQ,
)
from .utils import StringEnum

_COUNTER = 0


def _param_suffix() -> str:
    global _COUNTER
    _COUNTER += 1
    return (
        "_" + "".join(random.choices(string.ascii_letters, k=4)) + str(_COUNTER)
    )


class Condition(ABC):
    values: Dict[str, AttributeValue] = {}
    attributes: Set[str]

    def __init__(self, **kwargs):
        self.attributes = set()
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
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "attribute_exists({attribute})"


class AttributeNotExists(Condition):
    def __init__(self, attribute: AbstractAttribute):
        super().__init__(attribute=str(attribute))
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "attribute_not_exists({attribute})"


class BeginsWithCondition(Condition):
    def __init__(self, attribute: AbstractAttribute, value: str):
        param_name = f":{attribute}{_param_suffix()}"
        super().__init__(attribute=str(attribute), value=param_name)
        self.values = {param_name: {"S": str(value)}}
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "begins_with({attribute}, {value})"


class ContainsCondition(Condition):
    def __init__(self, attribute: AbstractAttribute, value: Any):
        param_name = f":{attribute}{_param_suffix()}"
        if attribute.type not in (
            AttributeType.STRING,
            AttributeType.STRING_SET,
            AttributeType.NUMBER_SET,
            AttributeType.BINARY_SET,
        ):
            raise ValueError(
                f"Attribute `{attribute}` does not support `contains` function."
            )

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

        super().__init__(attribute=str(attribute), value=param_name)
        serializer = serializer_registry.get_for(type(value))
        self.values = {
            param_name: serialize_value(serializer.extract(value)),
        }
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "contains({attribute}, {value})"


class AttributeIsType(Condition):
    def __init__(
        self, attribute: AbstractAttribute, expected_type: AttributeType
    ):
        param_name = f":{attribute}{_param_suffix()}"
        super().__init__(attribute=str(attribute), expected_type=param_name)
        self.values = {param_name: {"S": str(expected_type)}}
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "attribute_type({attribute}, {expected_type})"


class LogicalCondition(Condition, ABC):
    def __init__(
        self,
        left_condition: Union[Condition, str],
        right_condition: Union[Condition, str],
    ):
        super().__init__(
            left_condition=left_condition, right_condition=right_condition
        )
        self.left_condition = left_condition
        self.right_condition = right_condition
        self.attributes = set()
        if isinstance(self.left_condition, Condition):
            self.attributes = self.left_condition.attributes
        if isinstance(self.right_condition, Condition):
            self.attributes = self.attributes | self.right_condition.attributes

    @cachedproperty
    def values(self) -> Dict[str, AttributeValue]:
        values: Dict[str, AttributeValue] = {}
        if isinstance(self.left_condition, Condition):
            values = self.left_condition.values

        if isinstance(self.right_condition, Condition):
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
        super().__init__(condition=condition)

    @property
    def format(self) -> str:
        return "(NOT {condition})"


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
        right_operand: Any,
    ):
        self.values = {}
        if isinstance(right_operand, AbstractAttribute):
            super().__init__(
                operator=operator,
                left_operand=left_operand,
                right_operand=right_operand,
            )
            self.attributes.add(left_operand.name)
            self.attributes.add(right_operand.name)
            return

        if isinstance(right_operand, Condition):
            raise ValueError(
                f"Could not compare `{left_operand}` "
                f"with a condition expression."
            )

        # validate value type
        AttributeType.from_python_type(type(right_operand))
        param_name = f":{left_operand}{_param_suffix()}"
        super().__init__(
            operator=operator,
            left_operand=left_operand,
            right_operand=param_name,
        )
        self.values = {param_name: left_operand.extract(right_operand)}
        self.attributes.add(left_operand.name)

    @property
    def format(self) -> str:
        return "{left_operand} {operator} {right_operand}"


class SizeCondition(Condition):
    def __init__(self, attribute: AbstractAttribute):
        super().__init__(attribute=attribute.name)
        self.values = {}
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        if "operator" not in self.format_params:
            return "size({attribute})"

        return "size({attribute}) {operator} {value}"

    def __eq__(self, value: int) -> SizeCondition:  # type: ignore
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


class BetweenCondition(Condition):
    def __init__(
        self,
        attribute: AbstractAttribute,
        a: Union[AbstractAttribute, str],
        b: Union[AbstractAttribute, str],
    ):
        params: Dict[str, str] = {}
        values: Dict[str, AttributeValue] = {}
        if not isinstance(a, AbstractAttribute):
            params["a"] = f":{attribute}_a{_param_suffix()}"
            values[params["a"]] = attribute.extract(a)
        else:
            params["a"] = str(a)

        if not isinstance(b, AbstractAttribute):
            params["b"] = f":{attribute}_b{_param_suffix()}"
            values[params["b"]] = attribute.extract(b)
        else:
            params["b"] = str(b)

        super().__init__(attribute=str(attribute), a=params["a"], b=params["b"])
        self.values = values
        self.attributes.add(attribute.name)

    @property
    def format(self) -> str:
        return "{attribute} BETWEEN {a} AND {b}"
