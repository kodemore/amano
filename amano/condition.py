from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Any

from .base_attribute import AbstractAttribute, AttributeType
from .constants import CONDITION_COMPARATOR_EQ, CONDITION_COMPARATOR_NEQ, \
    CONDITION_COMPARATOR_LT, CONDITION_COMPARATOR_LTE, CONDITION_COMPARATOR_GT, \
    CONDITION_COMPARATOR_GTE
from .utils import StringEnum

_COUNTER = 0


def _rand_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return "".join(random.choices(string.ascii_letters, k=4)) + str(_COUNTER)


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
    def __init__(self, left_condition: Union[Condition, str], right_condition: Union[Condition, str]):
        super().__init__(left_condition=left_condition, right_condition=right_condition)
        self._values = {}
        if hasattr(left_condition, "values"):
            self._values = left_condition.values

        if hasattr(right_condition, "values"):
            self._values = {**self._values, **right_condition.values}


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

    def __init__(self, operator: ComparisonOperator, attribute: AbstractAttribute, value: Any):
        if isinstance(value, AbstractAttribute):
            super().__init__(operator=operator, attribute=attribute, value=value)
            return

        if isinstance(value, Condition):
            raise ValueError(f"Could not compare `{attribute}` with a condition expression.")

        # validate value type
        AttributeType.from_python_type(type(value))
        value_name = f":{attribute}_{_rand_id()}"
        self._values = {value_name: attribute.extract(value)}
        super().__init__(operator=operator, attribute=attribute, value=value_name)

    @property
    def format(self) -> str:
        return "{attribute} {operator} {value}"

    @property
    def values(self) -> Dict[str, Dict[str, str]]:
        return self._values
