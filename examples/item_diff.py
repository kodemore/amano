from amano.item import Item, get_item_state, commit, diff


class Forum(Item):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0

    def __init__(self, name: str, category: str) -> None:
        self.forum_name = name
        self.category = category


item = Forum("Forum Name", "Category")
item.forum_name = "New Name"

print(diff(item))
# ('SET forum_name = :forum_name ', {':forum_name': 'New Name'})
