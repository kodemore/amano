# Basic Usage

--8<-- "docs/examples_header.md"


## Storing Items

To store Item, you can use the `put` or `save` method of `amano.Table` class.
The difference between those two methods is that `save` can understand state of the Item and can execute either `PutItem` or `UpdateItem` operation depending on the scenario. 

On the other hand, the `Put` method always executes `PutItem` expression. Which creates or fully overrides existing Item in case where no condition is provided.

> Both `put` and `save` methods allow using conditional expressions.

```python title="Using put method"
--8<-- "docs/examples/table_storing_items.py"
```


## Retrieving Items

Dynamodb allows to choose between two types of primary keys:
- __Partition key__. It is a simplified primary key. It means there 
should be no two items in a table with the same partition key value.
- __Composite key__. It is a combination of the partition key and sort key. 
This means there might be items in a table with the same partition key, but they must have different sort key values.


### Retrieving by a partition key
```python title="Get an item by a partition key"
--8<-- "docs/examples/table_get_by_partition_key.py"
```

### Retrieving by a composite key

```python

```


## Updating Items

`Table.update` edits an existing item's attributes. The difference between `put` and `update` is that update calculates Item's changes and performs a query only for the attributes that were changed. To update an Item, it must be retrieved first.

```python
from dataclasses import dataclass

import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

@dataclass
class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

forum_table = Table[Forum](client, table_name="Forum")
amano_forum = forum_table.get("Amano Forum")
amano_forum.Category = "Other Category"

assert forum_table.update(amano_forum)
```

## Deleting Items

```python
from dataclasses import dataclass

import boto3
from amano import Table, Item

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
```
