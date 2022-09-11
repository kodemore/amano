from __future__ import annotations
import inspect

from typing import Any, Generic, TypeVar, Type

from .base_attribute import (
    AttributeType,
    AbstractAttribute,
    serializer_registry,
    serialize_value,
    deserialize_value,
    _SUPPORTED_BASE_TYPES
)
from .condition import (
    ComparisonCondition,
    AttributeExists,
    AttributeNotExists,
    AttributeIsType,
    BeginsWithCondition,
    ContainsCondition,
    SizeCondition, BetweenCondition,
)


_T = TypeVar('_T')


class Attribute(AbstractAttribute, Generic[_T]):
    def __init__(
        self, name: str, attribute_type: type, default_value: Any = None
    ):
        self.name = name
        if inspect.isclass(attribute_type) and\
                issubclass(attribute_type, Attribute):
            if not attribute_type.__attribute_type__:
                raise TypeError(
                    f"Cannot use non parametrized Attribute `{name}` as a value"
                )
            attribute_type = attribute_type.__attribute_type__

        self.type = AttributeType.from_python_type(attribute_type)
        self._strategy = serializer_registry.get_for(
            attribute_type,
            strict=True
        )
        self.default_value = default_value

    def extract(self, value: Any) -> Any:
        return serialize_value(self._strategy.extract(value))

    def hydrate(self, value: Any) -> Any:
        return self._strategy.hydrate(deserialize_value(value))

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f'Attribute[{self.type}]("{self.name}")'

    def __eq__(self, other) -> ComparisonCondition:  # type: ignore
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.EQ, self, other
        )

    def __gt__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.GT, self, other
        )

    def __ge__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.GTE, self, other
        )

    def __lt__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.LT, self, other
        )

    def __le__(self, other) -> ComparisonCondition:
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.LTE, self, other
        )

    def not_exists(self) -> AttributeNotExists:
        return AttributeNotExists(self)

    def exists(self) -> AttributeExists:
        return AttributeExists(self)

    def is_type(self, attribute_type: AttributeType) -> AttributeIsType:
        return AttributeIsType(self, attribute_type)

    def startswith(self, string: str) -> BeginsWithCondition:
        return self.begins_with(string)

    def begins_with(self, string: str) -> BeginsWithCondition:
        return BeginsWithCondition(self, string)

    def contains(self, value: Any) -> ContainsCondition:
        return ContainsCondition(self, value)

    def between(self, a: Any, b: Any) -> BetweenCondition:
        return BetweenCondition(self, a, b)

    def size(self) -> SizeCondition:
        return SizeCondition(self)

    @classmethod
    def __class_getitem__(cls, item: Type[Any]) -> Type[Attribute]:
        if item not in _SUPPORTED_BASE_TYPES:
            raise TypeError(f"Unsupported generic subtype {item}")

        return type(  # type: ignore
            f"Attribute[{item}]",
            tuple([Attribute]),
            {"__attribute_type__": item}
        )
