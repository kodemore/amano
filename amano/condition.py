from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Any

from astroid.decorators import cachedproperty

from .base_attribute import AbstractAttribute, AttributeType, AttributeValue
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
    values: List

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
        self._values = {}
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
        self._values = {param_name: left_operand.extract(right_operand)}
        super().__init__(
            operator=operator,
            left_operand=left_operand,
            right_operand=param_name
        )

    @property
    def format(self) -> str:
        return "{left_operand} {operator} {right_operand}"

    @property
    def values(self) -> Dict[str, AttributeValue]:
        return self._values
