from amano import Table, Item
import boto3

client = boto3.client("dynamodb")


class Thread(Item):
    ForumName: str
    Subject: str
    Message: str
    LastPostedBy: str
    Replies: int = 0
    Views: int = 0


forum_table = Table[Thread](client, table_name="Thread")

cursor = forum_table.query(
    key_condition=(Thread.ForumName == "Amazon DynamoDB")
)
for item in cursor:
    print(item)
