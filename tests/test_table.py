import pytest

from amano import Index, Item, Table
from amano.index import PrimaryKey


def test_can_instantiate(readonly_dynamodb_client, readonly_table) -> None:
    # given
    class Track(Item):
        artist_name: str
        album_name: str
        track_name: str
        genre_name: str

    # when
    my_table = Table[Track](readonly_dynamodb_client, table_name=readonly_table)

    # then
    assert isinstance(my_table, Table)
    assert my_table._item_class == Track


def test_fail_instantiation_on_non_parametrized_table(
    readonly_dynamodb_client, readonly_table
) -> None:
    # when
    with pytest.raises(
        TypeError, match=".* must be parametrized with a subtype of .*"
    ):
        Table(readonly_dynamodb_client, table_name=readonly_table)


def test_fail_instantiation_on_unknown_table(
    readonly_dynamodb_client,
) -> None:
    # given
    class TestItem(Item):
        pk: str
        sk: str

    # when
    with pytest.raises(ValueError):
        Table[TestItem](readonly_dynamodb_client, table_name="TestItem")


def test_can_retrieve_partition_key(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        artist_name: str
        track_name: str

    # when
    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # then
    assert my_table.partition_key == "artist_name"


def test_can_retrieve_sort_key(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        artist_name: str
        track_name: str

    # when
    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # then
    assert my_table.sort_key == "track_name"


def test_fails_when_item_has_no_pk_defined(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        _artist_name: str
        track_name: str

    # then
    with pytest.raises(AttributeError):
        Table[Track](readonly_dynamodb_client, readonly_table)


def test_fails_when_item_has_no_sk_defined(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        artist_name: str
        _track_name: str

    # then
    with pytest.raises(AttributeError):
        Table[Track](readonly_dynamodb_client, readonly_table)


def test_can_retrieve_indexes(readonly_dynamodb_client, readonly_table) -> None:
    # given
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str
        genre_name: str

    # when
    table = Table[Track](readonly_dynamodb_client, readonly_table)

    # then
    assert len(table.indexes) == 4
    assert list(table.indexes.keys()) == [
        "#",
        "GlobalGenreAndAlbumNameIndex",
        "GlobalAlbumAndTrackNameIndex",
        "LocalArtistAndAlbumNameIndex",
    ]
    assert all(isinstance(index, Index) for index in table.indexes.values())


def test_can_retrieve_available_indexes(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    # when
    table = Table[Track](readonly_dynamodb_client, readonly_table)
    available_indexes = table.indexes

    # then
    assert len(available_indexes) == 3
    assert PrimaryKey.NAME in available_indexes
    assert "GlobalAlbumAndTrackNameIndex" in available_indexes
    assert "LocalArtistAndAlbumNameIndex" in available_indexes
