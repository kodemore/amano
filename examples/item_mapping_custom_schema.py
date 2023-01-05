import boto3
from amano import Table, Item
from dataclasses import dataclass

client = boto3.client("dynamodb")


@dataclass
class Forum(Item, mapping={
    "forum_name": "ForumName",
    "category": "Category",
    "threads": "Threads",
    "messages": "Messages",
    "views": "Views",
}):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0


forum_table = Table[Forum](client, table_name="Forum")
