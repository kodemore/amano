from amano.item import from_dict, Item


class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0


item = from_dict(
    Forum,
    {
        "ForumName": "Forum Name",
        "Category": "Category Name"
    }
)
