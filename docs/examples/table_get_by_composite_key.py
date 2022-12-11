import boto3
from amano import Table, Item
from dataclasses import dataclass

client = boto3.client("dynamodb")


@dataclass
class Thread(Item):
    ForumName: str
    Subject: str
    Message: str
    LastPostedBy: str
    Replies: int = 0
    Views: int = 0


forum_table = Table[Thread](client, table_name="Thread")
forum_table.get("Amazon DynamoDB", "Tagging tables")
