from __future__ import annotations

import inspect
from typing import Any, Generic, Type, TypeVar

from .base_attribute import (
    _SUPPORTED_BASE_TYPES,
    AbstractAttribute,
    AttributeType,
    serializer_registry,
)
from .condition import (
    AttributeExists,
    AttributeIsType,
    AttributeNotExists,
    BeginsWithCondition,
    BetweenCondition,
    ComparisonCondition,
    ContainsCondition,
    SizeCondition,
)

_T = TypeVar('_T')


class Attribute(AbstractAttribute, Generic[_T]):
    def __init__(
        self, name: str, attribute_type: type, default_factory: callable = None # noqa: 501
    ):
        self.name = name
        if inspect.isclass(attribute_type) and issubclass(
            attribute_type, Attribute
        ):
            if not attribute_type.__attribute_type__:
                raise TypeError(
                    f"Cannot use non parametrized Attribute `{name}` as a value"
                )
            attribute_type = attribute_type.__attribute_type__

        self.type = AttributeType.from_python_type(attribute_type)
        self._strategy = serializer_registry.get_for(
            attribute_type, strict=True
        )
        self.default_factory = default_factory

    @property
    def default_value(self) -> Any:
        if not self.default_factory:
            return None
        return self.default_factory()

    def extract(self, value: Any) -> Any:
        return self._strategy.extract(value)

    def hydrate(self, value: Any) -> Any:
        return self._strategy.hydrate(value)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f'Attribute[{self.type}]("{self.name}")'

    def __eq__(self, other) -> ComparisonCondition:  # type: ignore
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.EQ, self, other
        )

    def __ne__(self, other) -> ComparisonCondition:  # type: ignore
        return ComparisonCondition(
            ComparisonCondition.ComparisonOperator.NEQ, self, other
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
            {"__attribute_type__": item},
        )
