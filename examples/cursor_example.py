import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient

from amano import Table
from items import ThreadItem
from schemas import thread_schema, load_table_data

# bootstrap local dynamodb client
session = boto3.Session(
    aws_access_key_id="example",
    aws_secret_access_key="example",
    region_name="localhost",
)
client: DynamoDBClient = session.client(
    "dynamodb", endpoint_url="http://localhost:8000"
)


thread_schema.publish(client)
load_table_data(client, "examples/data/thread.json")

table = Table[ThreadItem](client, "Thread")

# fetch items on demand
for item in table.scan():
    assert isinstance(item, ThreadItem)


# fetch all items at once
items = table.scan().fetch()

# clean up
thread_schema.destroy(client)
