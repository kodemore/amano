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

# get an item
item = forum_table.get("Amano Forum", "Amazon DynamoDB")

# delete it
forum_table.delete(item)
