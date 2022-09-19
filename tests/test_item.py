from dataclasses import dataclass, field

from amano.attribute import Attribute, AttributeType
from amano.item import Item, _AttributeChange, _ChangeType, _ItemState


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
    assert "name" in MyItem
    assert "other_name" not in MyItem

    assert "other_name" in MyOtherItem
    assert "name" not in MyOtherItem


def test_can_get_attribute() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    # then
    assert "name" in MyItem
    assert "age" in MyItem
    assert isinstance(MyItem.name, Attribute)
    assert isinstance(MyItem.age, Attribute)

    assert MyItem.name.name == "name"
    assert MyItem.name.type == "S"
    assert MyItem.name.type == AttributeType.STRING

    assert MyItem.age.name == "age"
    assert MyItem.age.type == "N"
    assert MyItem.age.type == AttributeType.NUMBER


def test_can_get_attributes() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    assert [attribute.name for attribute in MyItem.attributes.values()] == [
        "name",
        "age",
    ]


def test_can_hydrate_item() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    # when
    item = MyItem.hydrate({"name": {"S": "Bobik"}, "age": {"N": "10"}})

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
    item = MyItem.hydrate(
        {"mapped_name": {"S": "Bobik"}, "mapped_age": {"N": "10"}}
    )

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
    value = item.extract()

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
    value = item.extract()

    # then
    assert value == {
        "mapped_name": {"S": "Bobik"},
        "mapped_age": {"N": "10"},
    }


def test_can_hydrate_item_as_dataclass() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int

    # when
    item = MyItem.hydrate({"name": {"S": "Bobik"}, "age": {"N": "10"}})

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
    value = item.extract()

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
        assert isinstance(log, _AttributeChange)

    assert item.__log__[0].type == _ChangeType.SET
    assert item.__log__[1].type == _ChangeType.SET
    assert item.__log__[2].type == _ChangeType.CHANGE
    assert item.__log__[3].type == _ChangeType.UNSET


def test_can_get_item_state() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int = 10

    # when
    item = MyItem("Bobik")

    # then
    assert item._state() == _ItemState.NEW
    assert item.name == "Bobik"
    assert item.age == 10

    # when
    item._commit()

    # then
    assert item._state() == _ItemState.CLEAN

    # when
    del item.age

    # then
    assert item._state() == _ItemState.DIRTY
