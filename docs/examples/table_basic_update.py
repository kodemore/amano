from amano import Table, Item
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
amano_forum = forum_table.get("Amano Forum")
amano_forum.Category = "Other Category"

assert forum_table.update(amano_forum)
