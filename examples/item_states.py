from amano.item import Item, get_item_state


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
print(get_item_state(item))  # ItemState.NEW

item.forum_name = "New Name"
print(get_item_state(item))  # ItemState.DIRTY
