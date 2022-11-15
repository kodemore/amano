import boto3
from mypy_boto3_dynamodb import DynamoDBClient

from amano import TableSchema, PrimaryKey, Attribute, GlobalSecondaryIndex, LocalSecondaryIndex
from items import ForumItem

# bootstrap local dynamodb client
session = boto3.Session(
    aws_access_key_id="example",
    aws_secret_access_key="example",
    region_name="localhost",
)
client: DynamoDBClient = session.client(
    "dynamodb", endpoint_url="http://localhost:8000"
)

# A Table has to define a primary key
forum_table = TableSchema("Forum", PrimaryKey(ForumItem.name))

# You can set a ttl for an item using one of its attributes
# or by defining a new one.
forum_table.enable_ttl(Attribute[int]("ttl"))

# Global secondary index
forum_table.add_index(GlobalSecondaryIndex("GSI", ForumItem.category))

# Local secondary index
forum_table.add_index(
    LocalSecondaryIndex("LSI", ForumItem.name, ForumItem.threads)
)

# You can also provision a table
forum_table.use_provisioning(10, 5)

# You can set tags
forum_table.tags["project"] = "test"

# And finally publish the table
forum_table.publish(client)

# Or simply remove it
forum_table.destroy(client)
