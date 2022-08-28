from __future__ import annotations

from decimal import Decimal
from typing import Any

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from chili import HydrationStrategy
from chili.hydration import StrategyRegistry

from .base_attribute import AttributeType, AbstractAttribute
from .condition import ComparisonCondition, Condition

_serialize_value = TypeSerializer().serialize
_deserialize_value = TypeDeserializer().deserialize


class FloatStrategy(HydrationStrategy):
    def hydrate(self, value: Any) -> float:
        return float(value)

    def extract(self, value: Any) -> Decimal:  # decimal is understood by dynamodb
        return Decimal(str(value))


_serializer_registry = StrategyRegistry()

# Add support for floats in dynamodb
_serializer_registry.add(float, FloatStrategy())


class Attribute(AbstractAttribute):
    def __init__(self, name: str, attribute_type: type, default_value: Any = None):
        self.name = name
        self.type = AttributeType.from_python_type(attribute_type)
        self.strategy = _serializer_registry.get_for(attribute_type, strict=True)
        self.default_value = default_value

    def extract(self, value: Any) -> Any:
        return _serialize_value(self.strategy.extract(value))

    def hydrate(self, value: Any) -> Any:
        return self.strategy.hydrate(_deserialize_value(value))

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Attribute[{self.type}](\"{self.name}\")"

    def __eq__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.EQ,
            self,
            other
        )

    def __gt__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.GT,
            self,
            other
        )

    def __ge__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.GTE,
            self,
            other
        )

    def __lt__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.LT,
            self,
            other
        )

    def __le__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.LTE,
            self,
            other
        )

    def not_exists(self) -> Condition:
        ...
