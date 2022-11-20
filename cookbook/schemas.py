from mypy_boto3_dynamodb.client import DynamoDBClient

from amano import PrimaryKey
from amano import TableSchema
from items import ForumItem, ThreadItem, ReplyItem
import os
import json

# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AppendixSampleTables.html

# Forum table
forum_schema = TableSchema("Forum", PrimaryKey(ForumItem.name))

# Thread table
thread_schema = TableSchema(
    "Thread", PrimaryKey(ThreadItem.forum_name, ThreadItem.subject)
)

# Reply table
reply_schema = TableSchema(
    "Reply", PrimaryKey(ReplyItem.id)
)


def publish_table_schema(client: DynamoDBClient, schema: TableSchema) -> None:
    try:
        client.delete_table(TableName=schema.table_name)
    except Exception:
        pass

    schema.publish(client)


def load_table_data(client: DynamoDBClient, filename: str) -> None:
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(base_dir, filename)
    data = json.load(open(file_path))

    client.batch_write_item(RequestItems=data)
