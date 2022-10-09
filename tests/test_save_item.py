from dataclasses import dataclass

from amano import Item, Table


def test_can_save_new_item(default_dynamodb_client, default_table) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    # when
    item = Track("Tool", "Reflection", "Lateralus")
    result = my_table.save(item)

    # then
    assert result
    assert my_table.get("Tool", "Reflection")


def test_can_save_modified_item(default_dynamodb_client, default_table) -> None:
    # given
    @dataclass
    class Track(Item):
        artist_name: str
        track_name: str
        album_name: str

    my_table = Table[Track](default_dynamodb_client, default_table)

    # when
    item = Track("Tool", "Reflection", "Lateralus")
    assert my_table.put(item)

    # then
    item.album_name = "New Album"
    assert my_table.save(item)
    result = my_table.get("Tool", "Reflection")
    assert result.album_name == "New Album"
