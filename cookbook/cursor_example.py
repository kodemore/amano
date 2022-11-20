from os import path

import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient

from amano import Table
from cookbook import BASE_DIR
from items import ThreadItem
from schemas import thread_schema, load_table_data

# Bootstrap local dynamodb client
session = boto3.Session(
    aws_access_key_id="example",
    aws_secret_access_key="example",
    region_name="localhost",
)
client: DynamoDBClient = session.client(
    "dynamodb", endpoint_url="http://localhost:8000"
)

# Create Thread table
thread_schema.publish(client)

# Load data from json file
load_table_data(client, "data/thread.json")

# Instantiate table
table = Table[ThreadItem](client, "Thread")

# Fetch items on demand and iterate through cursor
for item in table.scan():
    print(item)
    assert isinstance(item, ThreadItem)


# Fetch all items from cursor
items = table.scan().fetch()
print(items)

# By default, cursor is in a hydration mode. Hydration mode causes cursor to
# return instances of the `ThreadItem` class. You can disable hydration, like
# below to get items represented as dictionaries.
cursor = table.scan()
cursor.hydrate = False

items_as_dict = cursor.fetch()
print(items_as_dict)

# clean up
thread_schema.destroy(client)
