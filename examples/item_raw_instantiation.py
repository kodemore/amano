from amano.item import hydrate, Item


class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0


item = hydrate(
    Forum,
    {
        "ForumName": {"S": "Forum Name"},
        "Category": {"S": "Category Name"}
    }
)
