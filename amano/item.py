from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Type

from .attribute import Attribute


class _Undefined:
    def __repr__(self):
        return "UNDEFINED"


UNDEFINED = _Undefined()


class _ChangeType(Enum):
    SET = "SET"
    UNSET = "REMOVE"
    CHANGE = "CHANGE"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(\"{self.value}\")"


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
    def __new__(cls, what, bases, body, **meta) -> ItemMeta:
        if body["__module__"] == __name__ and what == "Item":
            return type.__new__(cls, what, bases, body)

        class_instance = type.__new__(
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
            for attribute_name, attribute_type in body["__annotations__"].items():
                class_instance.__meta__[attribute_name] = Attribute(
                    attribute_name, attribute_type, body[attribute_name] if attribute_name in body else UNDEFINED
                )

                setattr(class_instance, attribute_name, class_instance.__meta__[attribute_name])

        return class_instance

    @staticmethod
    def _get_table_attribute(attribute_name: str, item_class: Type[Item]) -> Attribute:
        if attribute_name in item_class:
            return item_class.__meta__[attribute_name]

        raise AttributeError(
            f"{item_class.__module__}.{item_class.__qualname__} does not specify any attribute with `{attribute_name}` name."
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
            for index, value in enumerate(args):
                item_data[self.attributes[index]] = value
        if kwargs:
            item_data = {**item_data, **kwargs}

        for attribute, value in item_data.items():
            setattr(self, attribute, value)

    def __getattribute__(self, key: str) -> Any:
        if key in ("__dict__", "__attributes__", "__log__", "__snapshots__", "__class__", "__meta__", "__module__"):
            return super().__getattribute__(key)

        if hasattr(self.__class__, key):
            if not isinstance(getattr(self.__class__, key), Attribute):
                return super().__getattribute__(key)

        if key not in self.__class__:
            raise AttributeError(f"Attribute {key} is not defined in {self.__class__} schema.")

        if key not in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

        return self.__dict__[key]

    def __setattr__(self, key, value):
        if key in self.__dict__:
            log_item = _AttributeChange(self.__meta__[key], _ChangeType.CHANGE, value)
        else:
            log_item = _AttributeChange(self.__meta__[key], _ChangeType.SET, value)

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
        return cls.__meta__.get(item)

    @classmethod
    @property
    def attributes(cls) -> List[str]:
        if not cls.__attributes__:
            cls.__attributes__ = list(cls.__meta__.keys())

        return cls.__attributes__

    @classmethod
    def hydrate(cls, value: Dict[str, Any]) -> Item:
        instance = cls.__new__(cls)

        for field, attribute in cls.__meta__.items():
            setattr(instance, field, attribute.hydrate(value.get(field)))

        instance._commit()
        return instance

    def extract(self) -> Dict[str, Any]:
        result = {}
        for field, attribute in self.__meta__.items():
            result[field] = attribute.extract(getattr(self, field))

        return result

    def _commit(self) -> None:
        commit = _Commit()
        for item in self.__log__:
            commit.add_change(item)

        self.__log__.clear()
        self.__snapshots__.append(commit)

    def _state(self) -> _ItemState:
        if not self.__log__ and len(self.__snapshots__) == 1:
            return _ItemState.CLEAN

        if not self.__snapshots__:
            return _ItemState.NEW

        return _ItemState.DIRTY


class VersionedItem(Item):
    ...
