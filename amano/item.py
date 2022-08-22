from __future__ import annotations

from collections import UserList
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Type, Any, List

from .attribute import Attribute


class _Undefined:
    def __repr__(self):
        return "UNDEFINED"


UNDEFINED = _Undefined()


class ChangeLog(UserList):
    ...


@dataclass
class ChangeLogEntry:
    class Type(Enum):
        SET = "set"
        UNSET = "unset"
        CHANGE = "change"

    name: str
    action: ChangeLogEntry.Type


class ItemMeta(type):
    def __new__(cls, what, bases, body, **meta) -> ItemMeta:
        if body["__module__"] == __name__ and what == "Item":
            return type.__new__(cls, what, bases, body)

        class_instance = type.__new__(cls, what, bases, {**body, **{
            "__meta__": {},
            "_attributes": [],
            "_changelog": ChangeLog(),
        }})

        if "__annotations__" in body:
            for attribute_name, attribute_type in body["__annotations__"].items():
                class_instance.__meta__[attribute_name] = Attribute(
                    attribute_name,
                    attribute_type,
                    body[attribute_name] if attribute_name in body else UNDEFINED
                )

                setattr(
                    class_instance,
                    attribute_name,
                    class_instance.__meta__[attribute_name]
                )

        return class_instance

    @staticmethod
    def _get_table_attribute(attribute_name: str, item_class: Type[Item]) -> Attribute:
        if attribute_name in item_class:
            return item_class.__meta__[attribute_name]

        raise AttributeError(f"{item_class.__module__}.{item_class.__qualname__} does not specify any attribute with `{attribute_name}` name.")

    def __init__(cls, name, bases, dct, **extra):
        super().__init__(name, bases, dct)

    def __contains__(self, item) -> bool:
        return item in self.__meta__


class Item(metaclass=ItemMeta):
    __meta__: Dict[str, Attribute]
    _attributes: List[str]
    _changelog: ChangeLog

    def __getattribute__(self, key: str) -> Any:
        if key in ("__dict__", "_attributes", "_logs", "__class__", "__meta__", "__module__"):
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
            log_item = ChangeLogEntry(key, ChangeLogEntry.Type.CHANGE)
        else:
            log_item = ChangeLogEntry(key, ChangeLogEntry.Type.SET)

        self._logs.append(log_item)

        if isinstance(value, Attribute):
            value = value.default_value

        super().__setattr__(key, value)

    def __delattr__(self, key: str) -> None:
        log_item = ChangeLogEntry(key, ChangeLogEntry.Type.UNSET)
        self._logs.append(log_item)
        del self.__dict__[key]

    @classmethod
    def __class_getitem__(cls, item: str) -> Attribute:
        return cls.__meta__.get(item)

    @classmethod
    @property
    def attributes(cls) -> List[str]:
        if not cls._attributes:
            cls._attributes = list(cls.__meta__.keys())

        return cls._attributes

    @classmethod
    def hydrate(cls, value: Dict[str, Any]) -> Item:
        instance = cls.__new__(cls)

        for field, attribute in cls.__meta__.items():
            setattr(instance, field, attribute.hydrate(value.get(field)))

        return instance

    def extract(self) -> Dict[str, Any]:
        result = {}
        for field, attribute in self.__meta__.items():
            result[field] = attribute.extract(getattr(self, field))

        return result

    def changelog(self) -> ChangeLog:
        return self._changelog
