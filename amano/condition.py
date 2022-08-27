from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Union, Any
from .base_attribute import AbstractAttribute, AttributeType
import string
import random


_COUNTER = 0


def _rand_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return "".join(random.choices(string.ascii_lowercase, k=4)) + str(_COUNTER)


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


class AndCondition(Condition):
    def __init__(self, left_condition: Union[Condition, str], right_condition: Union[Condition, str]):
        super().__init__(left_condition, right_condition)

    @property
    def format(self) -> str:
        return "({0} AND {1})"


class OrCondition(Condition):
    def __init__(self, left_condition: Union[Condition, str], right_condition: Union[Condition, str]):
        super().__init__(left_condition, right_condition)

    @property
    def format(self) -> str:
        return "({0} OR {1})"


class NotCondition(Condition):
    def __init__(self, condition: Union[Condition, str]):
        super().__init__(condition)

    @property
    def format(self) -> str:
        return "(NOT {0})"


class ComparisonCondition(Condition):
    class ComparisonOperator(Enum):
        EQ = '='
        NEQ = '<>'
        LT = '<'
        LTE = '<='
        GT = '>'
        GTE = '>='

        def __str__(self) -> str:
            return str(self.value)

    def __init__(self, operator: ComparisonOperator, attribute: AbstractAttribute, value: Any):
        if isinstance(value, AbstractAttribute):
            super().__init__(operator=operator, attribute=attribute, right_expression=value)
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
