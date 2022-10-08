from __future__ import annotations

from dataclasses import Field, dataclass
from enum import Enum
from inspect import isclass
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar, Union

from amano.attribute import Attribute

from .base_attribute import AttributeValue, deserialize_value, serialize_value
from .mapping import Mapping, MappingStrategy
from .undefined import UNDEFINED


@dataclass
class AttributeChange:
    class Type(Enum):
        SET = "SET"
        UNSET = "REMOVE"
        CHANGE = "CHANGE"

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}("{self.value}")'

    attribute: Attribute
    type: AttributeChange.Type
    value: Any


class Commit:
    log: List[AttributeChange]

    def __init__(self):
        self.log = []

    def append(self, change: AttributeChange) -> None:
        self.log.append(change)

    @property
    def changes(self) -> Dict[str, AttributeChange]:
        return {
            attribute_change.attribute.name: attribute_change
            for attribute_change in self.log
        }


ItemSchema = Dict[str, Attribute]
Diff = Tuple[str, Dict[str, Any]]


class ItemState(Enum):
    NEW = "new"
    CLEAN = "clean"
    DIRTY = "dirty"


def _create_init(base_init: Union[Callable, None]) -> Callable:
    def _init_item(item: Item, *args, **kwargs) -> None:
        item_data = {}
        for attribute in item.__schema__.values():
            item_data[attribute.name] = attribute.default_value

        if args:
            attribute_names = list(item.__schema__.keys())
            for index, value in enumerate(args):
                item_data[attribute_names[index]] = value
        if kwargs:
            item_data = {**item_data, **kwargs}

        for name, value in item_data.items():
            setattr(item, name, value)
        if base_init:
            base_init(item, *args, **kwargs)

    return _init_item


class ItemMeta(type):
    def __new__(cls, what, bases, body: dict, **meta) -> ItemMeta:
        class_module = body.get("__module__")

        # Skip the base item class
        if class_module == __name__ and what == "Item":
            return type.__new__(cls, what, bases, body)

        schema = ItemMeta._create_schema(
            ItemMeta._read_annotations(bases, body),
            ItemMeta._get_mapping(meta),
            body,
        )

        if "init" in meta and meta["init"] is True:
            body["__init__"] = _create_init(body.get("__init__"))

        new_class = type.__new__(
            cls,
            what,
            bases,
            {
                **body,
                **{
                    "__schema__": schema,
                    "__log__": [],
                    "__commits__": [],
                },
                **schema,
            },
        )

        return new_class

    @staticmethod
    def _create_schema(all_annotations, mapping, body):
        schema = {}
        for attr_name, attr_type in all_annotations.items():
            if isclass(attr_type) and issubclass(attr_type, Attribute):
                if not attr_type.__attribute_type__:
                    raise TypeError(f"Cannot parse generic {Attribute} type.")
                else:
                    attr_type = attr_type.__attribute_type__

            schema[attr_name] = ItemMeta._create_attribute(
                mapping[attr_name], attr_type, body.get(attr_name, UNDEFINED)
            )

        return schema

    @staticmethod
    def _create_attribute(attr_name: str, attr_type: type, field: Any):
        if isinstance(field, Field):
            if field.default_factory:
                return Attribute[attr_type](attr_name, field.default_factory)  # type: ignore

            return Attribute[attr_type](attr_name, lambda: field.default)  # type: ignore

        return Attribute[attr_type](attr_name, lambda: field)  # type: ignore

    @staticmethod
    def _get_mapping(meta):
        mapping = Mapping.PASS_THROUGH
        if "mapping" in meta:
            if not isinstance(
                meta["mapping"], MappingStrategy
            ) and not isinstance(meta, dict):
                raise TypeError(
                    f"mapping must be type of {MappingStrategy.__qualname__} "
                    f"or dict, {type(meta['mapping'])} passed instead."
                )
            mapping = meta["mapping"]

        return mapping

    @staticmethod
    def _read_annotations(bases, body):
        all_annotations = {}
        for base in bases:
            if base.__class__ == Item or base.__class__ == ItemMeta:
                continue
            if not hasattr(base, "__annotations__"):
                continue
            class_annotations = {
                att_name: att_type
                for att_name, att_type in getattr(
                    base, "__annotations__"
                ).items()
                if not att_name.startswith("_")
            }
            all_annotations = {**all_annotations, **class_annotations}
        if "__annotations__" in body:
            all_annotations = {**all_annotations, **body["__annotations__"]}

        return all_annotations

    def __init__(cls, name, bases, dct, **_):
        super().__init__(name, bases, dct)


class Item(metaclass=ItemMeta):
    __log__: List[AttributeChange]
    __schema__: ItemSchema
    __commits__: List[Commit]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattribute__(self, key: str) -> Any:
        if key.startswith("_") or key.isupper():
            return super().__getattribute__(key)

        if key not in self.__schema__:
            return super().__getattribute__(key)

        if key in self.__dict__:
            return self.__dict__[key]

        default_value = self.__schema__[key].default_value

        if default_value != UNDEFINED:
            return default_value

        raise AttributeError(
            f"Instance of `{self.__class__}` has no attribute `{key}`"
        )

    def __setattr__(self, key, value):
        if key not in self.__schema__:
            return super().__setattr__(key, value)

        if key in self.__dict__:
            log_item = AttributeChange(
                self.__schema__[key], AttributeChange.Type.CHANGE, value
            )
        else:
            log_item = AttributeChange(
                self.__schema__[key], AttributeChange.Type.SET, value
            )

        self.__log__.append(log_item)

        if isinstance(value, Attribute):
            value = value.default_value

        self.__dict__[key] = value

    def __delattr__(self, key: str) -> None:
        if key not in self.__dict__:
            return
        log_item = AttributeChange(
            self.__schema__[key], AttributeChange.Type.UNSET, None
        )
        self.__log__.append(log_item)
        del self.__dict__[key]


I = TypeVar("I", bound=Item)


def commit(item: Item) -> None:
    changes = Commit()
    for entry in item.__log__:
        changes.append(entry)

    item.__log__.clear()
    item.__commits__.append(changes)


def diff(item: Item) -> Diff:
    set_fields = []
    delete_fields = []
    attribute_values = {}

    for change in item.__log__:
        if change.type in (
            AttributeChange.Type.CHANGE,
            AttributeChange.Type.SET,
        ):
            set_fields.append(change.attribute.name)
            attribute_values[
                ":" + change.attribute.name
            ] = change.attribute.extract(change.value)
            continue
        if change.type is AttributeChange.Type.UNSET:
            delete_fields.append(change.attribute.name)

    update_expression = ""
    if set_fields:
        set_fields_expression = ','.join(
            [field_name + ' = :' + field_name for field_name in set_fields]
        )
        update_expression = f"SET {set_fields_expression} "
    if delete_fields:
        update_expression += (
            f"DELETE {','.join([field_name for field_name in set_fields])} "
        )

    return update_expression, attribute_values


def hydrate(what: Type[I], value: Dict[str, Any]) -> I:
    value = deserialize_value({"M": value})
    return from_dict(what, value)


def from_dict(what: Type[I], value: Dict[str, Any]) -> I:
    if not issubclass(what, Item):
        raise TypeError(
            f"Could not hydrate class {what.__qualname__}. expected "
            f"a subtype of {Item.__qualname__} class."
        )
    instance = what.__new__(what)
    for field, attribute in what.__schema__.items():
        if attribute.name not in value:
            continue
        setattr(instance, field, attribute.hydrate(value.get(attribute.name)))

    commit(instance)
    return instance


def extract(value: Item) -> Dict[str, AttributeValue]:
    return serialize_value(as_dict(value)).get("M")


def as_dict(value: Item) -> Dict[str, Any]:
    result = {}
    for field, attribute in value.__schema__.items():
        result[attribute.name] = attribute.extract(getattr(value, field))

    return result


def get_item_state(value: Item) -> ItemState:
    if not value.__log__ and len(value.__commits__) >= 1:
        return ItemState.CLEAN

    if not value.__commits__:
        return ItemState.NEW

    return ItemState.DIRTY
