from __future__ import annotations

from typing import Any, Callable, Generic, Type, TypeVar

from .base_attribute import (
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
        self,
        name: str,
        default_factory: Callable[[], Any] = None,
    ):
        if (
            not hasattr(self, "__attribute_type__")
            or not self.__attribute_type__
        ):  # noqa: E501
            raise TypeError(
                f"Cannot use non parametrized `{Attribute.__qualname__}` class as `{name}` field ."  # noqa: E501
            )
        self.name = name
        self.type = AttributeType.from_python_type(self.__attribute_type__)
        self._strategy = serializer_registry.get_for(
            self.__attribute_type__, strict=True
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
        return f'Attribute[{self.__attribute_type__.__name__}]("{self.name}")'

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
        return type(  # type: ignore
            f"{Attribute.__qualname__}[{item.__name__}]",
            tuple([Attribute]),
            {"__attribute_type__": item},
        )
