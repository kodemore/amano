from amano.item import extract, Item


class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

    def __init__(self, name: str, category: str):
        self.ForumName = name
        self.Category = category


item = Forum("Forum Name", "Forum Category")
print(extract(item))
