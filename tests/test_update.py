from dataclasses import dataclass

from amano import Attribute, Item, Table
from amano.item import ItemState, get_item_state


def test_can_update_item(default_dynamodb_client, default_table) -> None:
    # given
    @dataclass()
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    tracks = Table[Track](default_dynamodb_client, default_table)

    tracks.put(Track("AC/DC", "Let There Be Rock", "Let There Be Rock", "Rock"))

    track = tracks.get("AC/DC", "Let There Be Rock")
    assert isinstance(track, Track)

    # when
    track.album_name = "Undefined Album"
    tracks.update(track)

    # then
    assert get_item_state(track) == ItemState.CLEAN

    track = tracks.get("AC/DC", "Let There Be Rock")
    assert isinstance(track, Track)
    assert track.album_name == "Undefined Album"


def test_can_update_item_with_condition(
    default_dynamodb_client, default_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    tracks = Table[Track](default_dynamodb_client, default_table)

    tracks.put(Track("AC/DC", "Let There Be Rock", "Let There Be Rock", "Rock"))
    track = tracks.get("AC/DC", "Let There Be Rock")

    # when
    track.album_name = "Undefined Album"
    success = tracks.update(track, Track.album_name == "Let There Be Rock")

    # then
    assert success
    track = tracks.get("AC/DC", "Let There Be Rock")
    assert track.album_name == "Undefined Album"


def test_fail_update_item_with_condition(
    default_dynamodb_client, default_table
) -> None:
    # given
    class Track(Item, init=True):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    tracks = Table[Track](default_dynamodb_client, default_table)

    tracks.put(Track("AC/DC", "Let There Be Rock", "Let There Be Rock", "Rock"))
    track = tracks.get("AC/DC", "Let There Be Rock")

    # when
    track.album_name = "Undefined Album"
    success = tracks.update(track, Track.album_name != "Let There Be Rock")

    # then
    assert not success
    track = tracks.get("AC/DC", "Let There Be Rock")
    assert track.album_name == "Let There Be Rock"


def test_ignore_update_for_non_modified_item(
    default_dynamodb_client, default_table
) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: Attribute[str]
        track_name: Attribute[str]
        album_name: Attribute[str]
        genre_name: Attribute[str]

    tracks = Table[Track](default_dynamodb_client, default_table)

    track = Track("Artist", "Track", "Album", "Genre")
    tracks.put(track)
    assert get_item_state(track) == ItemState.CLEAN

    # when
    assert not tracks.update(track)

    # then
    assert get_item_state(track) == ItemState.CLEAN
