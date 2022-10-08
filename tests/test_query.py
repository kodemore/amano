from dataclasses import dataclass
from typing import Iterable

import pytest
from mypy_boto3_dynamodb import DynamoDBClient

from amano import Attribute, Item, Table
from amano.errors import AmanoDBError, ReadError


def test_can_query_item_by_pk_and_sk(
    readonly_dynamodb_client, readonly_table
) -> None:

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
    assert item.artist_name == "AC/DC"
    assert item.track_name == "Let There Be Rock"
    assert item.album_name == "Let There Be Rock"


def test_fail_query_item_by_pk_only(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    with pytest.raises(AmanoDBError) as e:
        item = my_table.get("AC/DC")

    # then
    assert isinstance(e.value, ReadError)


def test_query_table_with_pk_only(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str
        genre_name: str

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.query(Track.album_name == "Let There Be Rock")

    # then
    assert isinstance(result, Iterable)

    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 8


def test_query_table_with_pk_and_sk(
    readonly_dynamodb_client, readonly_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str
        genre_name: str

    my_table = Table[Track](readonly_dynamodb_client, readonly_table)

    # when
    result = my_table.query(
        (Track.artist_name == "AC/DC") & Track.track_name.startswith("S")
    )

    # then
    assert isinstance(result, Iterable)

    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 2


def test_query_table_with_pk_and_filter(
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
    result = my_table.query(
        key_condition=(Track.artist_name == "AC/DC"),
        filter_condition=Track.genre_name.startswith("R"),
    )

    # then
    assert isinstance(result, Iterable)

    assert result.count() == 18
    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 18


def test_query_table_with_limit(
    readonly_dynamodb_client: DynamoDBClient, readonly_table: str
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
    result = my_table.query(
        key_condition=(Track.artist_name == "AC/DC"),
        filter_condition=Track.genre_name.startswith("R"),
        limit=10,
    )

    # then
    assert isinstance(result, Iterable)

    assert result.count() == 10
    all_items = []
    for item in result:
        all_items.append(item)
        assert isinstance(item, Track)

    assert len(all_items) == 10


def test_query_table_returns_consumed_capacity(
    readonly_dynamodb_client: DynamoDBClient, readonly_table: str
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
    result = my_table.query(
        key_condition=(Track.artist_name == "AC/DC"),
        filter_condition=Track.genre_name.startswith("R"),
    )

    # then
    assert isinstance(result, Iterable)

    assert result.count() == 18
    assert result.consumed_capacity == 0.5
