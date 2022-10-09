from dataclasses import dataclass

from amano import Item, Table


def test_can_save_item(default_dynamodb_client, default_table) -> None:
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
