import pytest

from amano import Item, Table
from amano.errors import AmanoDBError, ItemNotFoundError


def test_get_item(readonly_dynamodb_client, readonly_table) -> None:

    # given
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    item = my_table.get("AC/DC", "Let There Be Rock")

    # then
    assert isinstance(item, Track)


def test_fail_get_unexisting_item(
    readonly_dynamodb_client, readonly_table
) -> None:

    # given
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    with pytest.raises(ItemNotFoundError) as e:
        item = my_table.get("AC/DC", "Let There Be No Rock")

    # then
    assert e.value.query == {
        "artist_name": "AC/DC",
        "track_name": "Let There Be No Rock",
    }
