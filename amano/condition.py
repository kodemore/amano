from __future__ import annotations

import random
import string
from abc import ABC
from typing import Any, Dict, List, Set, Union

from .base_attribute import (
    VALID_TYPE_VALUES,
    AbstractAttribute,
    AttributeType,
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
        "_"
        + "".join(random.choices(string.ascii_letters, k=4))  # nosec
        + str(_COUNTER)
    )


class Condition:
    def __init__(self, condition: str, parameters: Dict[str, Any] = None):
        self.condition = condition
        self.parameters = parameters or {}
        self.hint: Set[str] = set()  # hint for the index auto-resolving

    def __str__(self) -> str:
        return self.condition

    def __and__(self, other) -> AndCondition:
        return AndCondition(self, other)

    def __or__(self, other) -> OrCondition:
        return OrCondition(self, other)


class AttributeExists(Condition):
    CONDITION = "attribute_exists({attribute})"

    def __init__(self, attribute: AbstractAttribute):
        super().__init__(
            self.CONDITION.format(attribute=attribute.name),
        )
        self.hint.add(attribute.name)


class AttributeNotExists(Condition):
    CONDITION = "attribute_not_exists({attribute})"

    def __init__(self, attribute: AbstractAttribute):
        super().__init__(
            self.CONDITION.format(attribute=attribute.name),
        )
        self.hint.add(attribute.name)


class BeginsWithCondition(Condition):
    CONDITION = "begins_with({attribute}, {value})"

    def __init__(self, attribute: AbstractAttribute, value: str):
        param_name = f":{attribute}{_param_suffix()}"
        super().__init__(
            self.CONDITION.format(attribute=attribute.name, value=param_name),
            {param_name: value},
        )
        self.hint.add(attribute.name)


class ContainsCondition(Condition):
    CONDITION = "contains({attribute}, {value})"

    def __init__(self, attribute: AbstractAttribute, value: Any):
        param_name = f":{attribute}{_param_suffix()}"
        self._validate_attribute(attribute)
        self._validate_value(attribute, value)

        serializer = serializer_registry.get_for(type(value))

        super().__init__(
            self.CONDITION.format(attribute=attribute.name, value=param_name),
            {
                param_name: serializer.extract(value),  # type: ignore[dict-item]
            },
        )
        self.hint.add(attribute.name)

    def _validate_value(self, attribute, value) -> None:
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

    def _validate_attribute(self, attribute) -> None:
        if attribute.type not in (
            AttributeType.STRING,
            AttributeType.STRING_SET,
            AttributeType.NUMBER_SET,
            AttributeType.BINARY_SET,
        ):
            raise ValueError(
                f"Attribute `{attribute}` does not support `contains` function."
            )


class AttributeIsType(Condition):
    CONDITION = "attribute_type({attribute}, {expected_type})"

    def __init__(
        self, attribute: AbstractAttribute, expected_type: AttributeType
    ):
        param_name = f":{attribute}{_param_suffix()}"
        super().__init__(
            self.CONDITION.format(
                attribute=attribute.name, expected_type=param_name
            ),
            {param_name: str(expected_type)},
        )

        self.hint.add(attribute.name)


class LogicalCondition(Condition, ABC):
    CONDITION = ""

    def __init__(
        self,
        left_condition: Union[Condition, str],
        right_condition: Union[Condition, str],
    ):
        super().__init__(
            self.CONDITION.format(
                left_condition=left_condition, right_condition=right_condition
            ),
        )
        self.left_condition = left_condition
        self.right_condition = right_condition

        if isinstance(self.left_condition, Condition):
            self.parameters = {
                **self.parameters,
                **self.left_condition.parameters,
            }
            self.hint = self.left_condition.hint
        if isinstance(self.right_condition, Condition):
            self.parameters = {
                **self.parameters,
                **self.right_condition.parameters,
            }
            self.hint = self.hint | self.right_condition.hint


class AndCondition(LogicalCondition):
    CONDITION = "({left_condition} AND {right_condition})"


class OrCondition(LogicalCondition):
    CONDITION = "({left_condition} OR {right_condition})"


class NotCondition(Condition):
    CONDITION = "(NOT {condition})"

    def __init__(self, condition: Union[Condition, str]):
        super().__init__(self.CONDITION.format(condition=condition))


class ComparisonCondition(Condition):
    CONDITION = "{left_operand} {operator} {right_operand}"

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
        if isinstance(right_operand, Condition):
            raise ValueError(
                f"Could not compare `{left_operand}` "
                f"with a condition expression."
            )

        if isinstance(right_operand, AbstractAttribute):
            super().__init__(
                self.CONDITION.format(
                    left_operand=left_operand.name,
                    right_operand=right_operand.name,
                    operator=operator,
                )
            )
            self.hint.add(left_operand.name)
            self.hint.add(right_operand.name)
            return

        # validate value type
        AttributeType.from_python_type(type(right_operand))

        param_name = f":{left_operand}{_param_suffix()}"
        super().__init__(
            self.CONDITION.format(
                left_operand=left_operand.name,
                right_operand=param_name,
                operator=operator,
            ),
            {
                param_name: left_operand.extract(right_operand),
            },
        )
        self.hint.add(left_operand.name)


class SizeCondition(Condition):
    CONDITION = "size({attribute})"

    def __init__(self, attribute: AbstractAttribute):
        super().__init__(self.CONDITION.format(attribute=attribute.name))
        self.attribute = attribute

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
        param_name = f":{self.attribute.name}_size{_param_suffix()}"
        self.condition = f"{self.condition} {operator} {param_name}"

        self.parameters[param_name] = value

        return self


class BetweenCondition(Condition):
    CONDITION = "{attribute} BETWEEN {a} AND {b}"

    def __init__(
        self,
        attribute: AbstractAttribute,
        a: Union[AbstractAttribute, Any],
        b: Union[AbstractAttribute, Any],
    ):
        params: Dict[str, Any] = {}
        if not isinstance(a, AbstractAttribute):
            a_name = f":{attribute}_a{_param_suffix()}"
            params[a_name] = attribute.extract(a)
        else:
            a_name = a.name

        if not isinstance(b, AbstractAttribute):
            b_name = f":{attribute}_b{_param_suffix()}"
            params[b_name] = attribute.extract(b)
        else:
            b_name = b.name

        super().__init__(
            self.CONDITION.format(attribute=attribute.name, a=a_name, b=b_name),
            params,
        )

        self.hint.add(attribute.name)


class InCondition(Condition):
    CONDITION = "{attribute} IN ({values})"

    def __init__(
        self,
        attribute: AbstractAttribute,
        in_values: List[Union[AbstractAttribute, Any]],
    ):
        parameters: Dict[str, Any] = {}
        values: List[str] = []

        i = 0
        for value in in_values:
            if isinstance(value, AbstractAttribute):
                values.append(value.name)
                continue

            name = f":{attribute}_{i}{_param_suffix()}"
            values.append(name)
            parameters[name] = attribute.extract(value)
            i += 1

        super().__init__(
            self.CONDITION.format(
                attribute=attribute.name, values=", ".join(values)
            ),
            parameters,
        )
