import boto3
from amano import Table, Item
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
forum_table.put(Forum(ForumName="Amano Forum", Category="Amazon DynamoDB"))
