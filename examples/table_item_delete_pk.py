from amano import Table, Item, item
import boto3
from dataclasses import dataclass

client = boto3.client("dynamodb")


@dataclass
class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0


forum_table = Table[Forum](client, table_name="Forum")

# Delete item by PK (ForumName)
forum_table.delete(item.from_dict(Forum, {"ForumName": "name"}))
