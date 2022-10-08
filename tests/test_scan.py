from dataclasses import dataclass
from typing import Iterable

from amano import Attribute, Item, Table


def test_scan_table(readonly_dynamodb_client, readonly_table) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.scan()

    # then
    assert isinstance(result, Iterable)
    assert result.count() == 200

    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 200


def test_scan_table_with_filter(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.scan(
        (Track.artist_name == "AC/DC") & (Track.genre_name.startswith("R"))
    )

    # then
    assert isinstance(result, Iterable)
    assert result.count() == 18

    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 18


def test_scan_table_with_limit(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.scan(limit=30)

    # then
    assert isinstance(result, Iterable)

    assert result.count() == 30
    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 30


def test_scan_table_with_index(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.scan(use_index="GlobalAlbumAndTrackNameIndex")

    # then
    assert isinstance(result, Iterable)

    assert result.count() == 200
    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 200
