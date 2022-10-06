from dataclasses import dataclass, field
from typing import List

from amano import Mapping
from amano.attribute import Attribute, AttributeType
from amano.item import (
    AttributeChange,
    Item,
    ItemState,
    as_dict,
    commit,
    extract,
    from_dict,
    get_item_state,
    hydrate,
)


def test_can_instantiate() -> None:
    # given
    class MyItem(Item):
        name: str

    # when
    item = MyItem()

    # then
    assert isinstance(item, MyItem)
    assert isinstance(item, Item)


def test_has_attribute() -> None:
    # given
    class MyItem(Item):
        name: str

    class MyOtherItem(Item):
        other_name: str

    # then
    assert "name" in MyItem.__schema__
    assert isinstance(MyItem.name, Attribute)
    assert "other_name" not in MyItem.__schema__

    assert "other_name" in MyOtherItem.__schema__
    assert isinstance(MyOtherItem.other_name, Attribute)
    assert "name" not in MyOtherItem.__schema__


def test_can_get_attribute() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    # then
    assert "name" in MyItem.__schema__
    assert "age" in MyItem.__schema__
    assert isinstance(MyItem.name, Attribute)
    assert isinstance(MyItem.age, Attribute)

    assert MyItem.name.name == "name"
    assert MyItem.name.type == "S"
    assert MyItem.name.type == AttributeType.STRING

    assert MyItem.age.name == "age"
    assert MyItem.age.type == "N"
    assert MyItem.age.type == AttributeType.NUMBER


def test_can_hydrate_item() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    # when
    item = hydrate(MyItem, {"name": {"S": "Bobik"}, "age": {"N": "10"}})

    # then
    assert item.name == "Bobik"
    assert item.age == 10


def test_can_hydrate_item_with_mapping() -> None:
    # given
    field_mapping = {
        # class : table
        "name": "mapped_name",
        "age": "mapped_age",
    }

    class MyItem(Item, mapping=field_mapping):
        name: str
        age: int

    # when
    item = hydrate(
        MyItem, {"mapped_name": {"S": "Bobik"}, "mapped_age": {"N": "10"}}
    )

    # then
    assert item.name == "Bobik"
    assert item.age == 10


def test_can_hydrate_item_with_mapping_strategy() -> None:
    # given
    class MyItem(Item, mapping=Mapping.PASCAL_CASE):
        name: str
        age: int

    # when
    item = hydrate(MyItem, {"Name": {"S": "Bobik"}, "Age": {"N": "10"}})

    # then
    assert item.name == "Bobik"
    assert item.age == 10


def test_can_extract_item() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    item = MyItem("Bobik", 10)

    # when
    value = extract(item)

    # then
    assert value == {
        "name": {"S": "Bobik"},
        "age": {"N": "10"},
    }


def test_can_extract_item_with_mapping() -> None:
    # given
    field_mapping = {
        # class : table
        "name": "mapped_name",
        "age": "mapped_age",
    }

    class MyItem(Item, mapping=field_mapping):
        name: str
        age: int

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    item = MyItem("Bobik", 10)

    # when
    value = extract(item)

    # then
    assert value == {
        "mapped_name": {"S": "Bobik"},
        "mapped_age": {"N": "10"},
    }


def test_can_extract_item_with_mapping_strategy() -> None:
    # given
    class MyItem(Item, mapping=Mapping.PASCAL_CASE):
        name: str
        age: int

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    item = MyItem("Bobik", 10)

    # when
    value = extract(item)

    # then
    assert value == {
        "Name": {"S": "Bobik"},
        "Age": {"N": "10"},
    }


def test_can_hydrate_item_as_dataclass() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int

    # when
    item = hydrate(MyItem, {"name": {"S": "Bobik"}, "age": {"N": "10"}})

    # then
    assert item.name == "Bobik"
    assert item.age == 10


def test_can_extract_item_as_dataclass() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int

    item = MyItem("Bobik", 10)

    # when
    value = extract(item)

    # then
    assert value == {
        "name": {"S": "Bobik"},
        "age": {"N": "10"},
    }


def test_item_log() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int = 10

    # when
    item = MyItem("Bobik")

    # then
    assert item.name == "Bobik"
    assert item.age == 10
    assert len(item.__log__) == 2

    # when
    item.name = "Pluto"

    # then
    assert item.name == "Pluto"
    assert item.age == 10
    assert len(item.__log__) == 3

    # when
    del item.name

    # then
    assert not hasattr(item, "name")
    assert item.age == 10
    assert len(item.__log__) == 4

    for log in item.__log__:
        assert isinstance(log, AttributeChange)

    assert item.__log__[0].type == AttributeChange.Type.SET
    assert item.__log__[1].type == AttributeChange.Type.SET
    assert item.__log__[2].type == AttributeChange.Type.CHANGE
    assert item.__log__[3].type == AttributeChange.Type.UNSET


def test_use_default_values() -> None:
    # given
    @dataclass()
    class MyItem(Item):
        name: str
        age: int = 10
        tags: List[str] = field(default_factory=list)

    # when
    item = MyItem("Bobik")

    # then
    assert item.name == "Bobik"
    assert item.age == 10
    assert item.tags == []


def test_can_get_item_state() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int = 10

        def __init__(self, name: str):
            self.name = name

    # when
    item = MyItem("Bobik")

    # then
    assert get_item_state(item) == ItemState.NEW
    assert item.name == "Bobik"
    assert item.age == 10

    # when
    commit(item)

    # then
    assert get_item_state(item) == ItemState.CLEAN

    # when
    del item.name

    # then
    assert get_item_state(item) == ItemState.DIRTY


def test_can_init_item() -> None:
    # given
    class MyItem(Item, init=True):
        name: str
        age: int = 10

    # when
    item = MyItem(name="Bob")

    # then
    assert item.name == "Bob"
    assert item.age == 10


def test_can_override_init_item() -> None:
    # given
    class MyItem(Item, init=True):
        name: str
        age: int = 10

        def __init__(self, *_, **__):
            self.name = "Super " + self.name

    # when
    item = MyItem(name="Bob")

    # then
    assert item.name == "Super Bob"
    assert item.age == 10


def test_can_create_item_from_dict() -> None:
    # given
    @dataclass()
    class MyItem(Item):
        name: str
        age: int = 10
        tags: List[str] = field(default_factory=list)

    # when
    item = from_dict(MyItem, {"name": "Bob", "age": 21})

    # then
    assert isinstance(item, MyItem)
    assert item.name == "Bob"
    assert item.age == 21
    assert item.tags == []


def test_can_represent_item_as_dict() -> None:
    # given
    @dataclass()
    class MyItem(Item):
        name: str
        age: int = 10
        tags: List[str] = field(default_factory=list)

    # when
    item = as_dict(MyItem(name="Bob", age=21))

    # then
    assert item["name"] == "Bob"
    assert item["age"] == 21
    assert item["tags"] == []
