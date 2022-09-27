from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Type, TypeVar, Union

from .attribute import Attribute
from .base_attribute import AttributeValue


class MappingStrategy(ABC):
    @abstractmethod
    def __getitem__(self, item: str) -> str:
        ...

    def __contains__(self, item: str) -> bool:
        return True


class PassThroughMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item

    def __contains__(self, item) -> bool:
        return False


class HyphensMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return item.replace("_", "-")


class PascalCaseMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        def upper_first(val: str) -> str:
            if len(val) > 1:
                return val[0].upper() + val[1:]
            return val.upper()

        camel_case = reduce(lambda x, y: x + upper_first(y), item.split("_"))
        if len(camel_case) > 1:
            return camel_case[0].upper() + camel_case[1:]
        return camel_case.upper()


class CamelCaseMapping(MappingStrategy):
    def __getitem__(self, item: str) -> str:
        return reduce(lambda x, y: x + y.capitalize(), item.split("_"))


class Mapping(Enum):
    PASS_THROUGH = PassThroughMapping()
    PASCAL_CASE = PascalCaseMapping()
    CAMEL_CASE = CamelCaseMapping()
    HYPHENS = HyphensMapping()

    def __getitem__(self, item: str) -> str:
        return self.value[item]

    def __contains__(self, item) -> bool:
        return item in self.value


class _Undefined:
    def __repr__(self):
        return "UNDEFINED"


UNDEFINED = _Undefined()


class _ChangeType(Enum):
    SET = "SET"
    UNSET = "REMOVE"
    CHANGE = "CHANGE"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'


@dataclass
class _AttributeChange:
    attribute: Attribute
    type: _ChangeType
    value: Any


class _Commit:
    changes: List[_AttributeChange]
    data: Dict[str, Any]

    def __init__(self):
        self.changes = []
        self.data = {}

    def add_change(self, change: _AttributeChange) -> None:
        self.changes.append(change)
        if change.type in (_ChangeType.SET, _ChangeType.CHANGE):
            self.data[str(change.attribute)] = change.value
            return

        del self.data[str(change.attribute)]


class ItemMeta(type):
    __meta__: Dict[str, Attribute]

    def __new__(cls, what, bases, body, **meta) -> ItemMeta:
        if body["__module__"] == __name__ and what == "Item":
            return type.__new__(cls, what, bases, body)

        new_class = type.__new__(
            cls,
            what,
            bases,
            {
                **body,
                **{
                    "__meta__": {},
                    "__attributes__": [],
                    "__log__": [],
                    "__snapshots__": [],
                },
            },
        )

        if "__annotations__" in body:
            if "mapping" in meta:
                mapping = meta["mapping"]
            else:
                mapping = Mapping.PASS_THROUGH
            for attribute_name, attribute_type in body[
                "__annotations__"
            ].items():
                new_class.__meta__[attribute_name] = Attribute(  # type: ignore[abstract]
                    attribute_name
                    if attribute_name not in mapping
                    else mapping[attribute_name],
                    attribute_type,
                    body[attribute_name]
                    if attribute_name in body
                    else UNDEFINED,
                )

                setattr(
                    new_class,
                    attribute_name,
                    new_class.__meta__[attribute_name],
                )

        return new_class

    @staticmethod
    def _get_table_attribute(
        attribute_name: str, item_class: Type[Item]
    ) -> Attribute:
        if attribute_name in item_class:
            return item_class.__meta__[attribute_name]

        raise AttributeError(
            f"{item_class.__module__}.{item_class.__qualname__} "
            f"does not specify any attribute with `{attribute_name}` name."
        )

    def __init__(cls, name, bases, dct, **extra):
        super().__init__(name, bases, dct)

    def __contains__(self, item) -> bool:
        return item in self.__meta__


class _ItemState(Enum):
    NEW = "new"
    CLEAN = "clean"
    DIRTY = "dirty"


class Item(metaclass=ItemMeta):
    __meta__: Dict[str, Attribute]
    __attributes__: List[str]
    __log__: List[_AttributeChange]
    __snapshots__: List[_Commit]

    def __init__(self, *args, **kwargs) -> None:
        item_data = {}
        for attribute in self.__meta__.values():
            item_data[attribute.name] = attribute.default_value

        if args:
            attribute_names = list(self.attributes.keys())
            for index, value in enumerate(args):
                item_data[attribute_names[index]] = value
        if kwargs:
            item_data = {**item_data, **kwargs}

        for name, value in item_data.items():
            setattr(self, name, value)

    def __getattribute__(self, key: str) -> Union[Attribute, Any]:
        if key in (
            "__dict__",
            "__attributes__",
            "__log__",
            "__snapshots__",
            "__class__",
            "__meta__",
            "__module__",
        ):
            return super().__getattribute__(key)

        if hasattr(self.__class__, key):
            if not isinstance(getattr(self.__class__, key), Attribute):
                return super().__getattribute__(key)

        if key not in self.__class__:
            raise AttributeError(
                f"Attribute {key} is not defined in {self.__class__} schema."
            )

        if key not in self.__dict__:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            )

        return self.__dict__[key]

    def __setattr__(self, key, value):
        if key in self.__dict__:
            log_item = _AttributeChange(
                self.__meta__[key], _ChangeType.CHANGE, value
            )
        else:
            log_item = _AttributeChange(
                self.__meta__[key], _ChangeType.SET, value
            )

        self.__log__.append(log_item)

        if isinstance(value, Attribute):
            value = value.default_value

        super().__setattr__(key, value)

    def __delattr__(self, key: str) -> None:
        log_item = _AttributeChange(self.__meta__[key], _ChangeType.UNSET, None)
        self.__log__.append(log_item)
        del self.__dict__[key]

    @classmethod
    def __class_getitem__(cls, item: str) -> Attribute:
        return cls.__meta__[item]

    @classmethod
    @property
    def attributes(cls) -> Dict[str, Attribute]:
        return cls.__meta__

    @classmethod
    def hydrate(cls, value: Dict[str, AttributeValue]) -> Item:
        instance = cls.__new__(cls)

        for field, attribute in cls.__meta__.items():
            if attribute.name not in value:
                setattr(instance, field, None)
                continue
            setattr(
                instance, field, attribute.hydrate(value.get(attribute.name))
            )

        instance._commit()
        return instance

    def extract(self) -> Dict[str, AttributeValue]:
        result = {}
        for field, attribute in self.__meta__.items():
            result[attribute.name] = attribute.extract(getattr(self, field))

        return result

    def _commit(self) -> None:
        commit = _Commit()
        for item in self.__log__:
            commit.add_change(item)

        self.__log__.clear()
        self.__snapshots__.append(commit)

    def _state(self) -> _ItemState:
        if not self.__log__ and len(self.__snapshots__) >= 1:
            return _ItemState.CLEAN

        if not self.__snapshots__:
            return _ItemState.NEW

        return _ItemState.DIRTY

    def __str__(self) -> str:
        return f"{self.__class__}()"


class VersionedItem(Item):
    ...


I = TypeVar("I", bound=Item)
