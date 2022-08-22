from dataclasses import dataclass, field

from amano import Item, Attribute
from amano.item import ChangeLogEntry


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
    assert MyItem.name.type == Attribute.Type.STRING

    assert MyItem.age.name == "age"
    assert MyItem.age.type == "N"
    assert MyItem.age.type == Attribute.Type.NUMBER


def test_can_get_attributes() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    assert MyItem.attributes == ["name", "age"]


def test_can_hydrate_item() -> None:
    # given
    class MyItem(Item):
        name: str
        age: int

    # when
    item = MyItem.hydrate({"name": "Bobik", "age": "10"})

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
        "name": "Bobik",
        "age": 10,
    }


def test_can_hydrate_item_as_dataclass() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int

    # when
    item = MyItem.hydrate({"name": "Bobik", "age": "10"})

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
        "name": "Bobik",
        "age": 10,
    }


def test_item_changelog() -> None:
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
    assert len(item.changelog()) == 2

    # when
    item.name = "Pluto"

    # then
    assert item.name == "Pluto"
    assert item.age == 10
    assert len(item.changelog()) == 3

    # when
    del item.name

    # then
    assert not hasattr(item, "name")
    assert item.age == 10
    assert len(item.changelog()) == 4


def test_can_get_changelog_for_attribute() -> None:
    # given
    @dataclass
    class MyItem(Item):
        name: str
        age: int = 10

    item = MyItem("Bobik")

    # when
    item.name = "Pluto"
    del item.name
    item.name = "Bobik"

    # then
    changelog = item.changelog()

    assert len(changelog) == 4
    assert changelog[0].action == ChangeLogEntry.Type.SET
    assert changelog[1].action == ChangeLogEntry.Type.CHANGE
    assert changelog[2].action == ChangeLogEntry.Type.UNSET
    assert changelog[3].action == ChangeLogEntry.Type.SET
