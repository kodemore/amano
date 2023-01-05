from amano import Item


class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0


item = Forum(ForumName="Forum Name", Category="Category")
