from dataclasses import dataclass

import pytest

from amano import Item, Table
from amano.errors import ItemNotFoundError


def test_can_delete_item(default_dynamodb_client, default_table) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    item = Track("Tool", "Reflection", "Lateralus")
    assert my_table.put(item)
    assert my_table.get("Tool", "Reflection")

    # when
    assert my_table.delete(item)

    # then
    with pytest.raises(ItemNotFoundError):
        my_table.get("Tool", "Reflection")


def test_can_delete_unexisting_item(
    default_dynamodb_client, default_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    item = Track("Tool", "Reflection", "Lateralus")

    # when
    assert my_table.delete(item)


def test_can_delete_item_with_passing_condition(
    default_dynamodb_client, default_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    item = Track("Tool", "Reflection", "Lateralus")
    assert my_table.put(item)
    assert my_table.get("Tool", "Reflection")

    # when
    assert my_table.delete(item, Track.album_name == "Lateralus")

    # then
    with pytest.raises(ItemNotFoundError):
        my_table.get("Tool", "Reflection")


def test_can_delete_item_with_failing_condition(
    default_dynamodb_client, default_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    item = Track("Tool", "Reflection", "Lateralus")
    assert my_table.put(item)
    assert my_table.get("Tool", "Reflection")

    # when
    assert not my_table.delete(item, Track.album_name != "Lateralus")

    # then
    assert my_table.get("Tool", "Reflection")
