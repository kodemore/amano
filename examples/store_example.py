from datetime import datetime

import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient

from amano import Table
from items import ReplyItem
from schemas import reply_schema

# bootstrap local dynamodb client
session = boto3.Session(
    aws_access_key_id="example",
    aws_secret_access_key="example",
    region_name="localhost",
)
client: DynamoDBClient = session.client(
    "dynamodb", endpoint_url="http://localhost:8000"
)
reply_schema.publish(client)

table = Table[ReplyItem](client, reply_schema.table_name)

table.put(ReplyItem(
    id="example_reply",
    reply_date_time=datetime.utcnow(),
    message="Example message",
    posted_by="John Doe",
))

# clean up
reply_schema.destroy(client)
