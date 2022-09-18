# Amano DB

AWS DynamoDB Abstraction Layer build on Table Data Gateway Pattern.

## Features

    - Hydration and extraction of table items
    - Simple query mechanism
    - Interface for easy storing and retriving data
    - Mechanism which automatically picks index for your queries
    - Saves your DynamoDB quota for PAY_PER_REQUEST provisioning

## What Amano is

As mentioned above amano is a Table Data Gateway Patter implementation, which
means it relies on already existing schema of your table. It can understand
existing schema to simplify daily tasks like; storing, retrieving and query
data.
Amano has built-in mechanism to auto-picking index. This means as long as there
might be an index to perform a query against your table amano will automatically
pick the best matching index for your query.

## Basic Usage
Following examples rely on [AWS Discussion Forum Data Model](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SampleData.CreateTables.html#SampleData.CreateTables2).

### Defining your first Item

The example below defines a `Forum` class, which is a representation of a 
record in a dynamodb's table. This class is required to instantiate parametrized
`Table` class that abstract access do dynamodb's table.

```python
import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

forum_table = Table[Forum](client, table_name="Forum")
```

> Please note: `Forum` class extends `amano.Item` class. This is required 
> by `amano.Table` to properly work. 


### Storing item in a table

To store item, you can use the `put` or `save` method of `amano.Table` class.
The difference between those two methods is that `save` can execute either 
`PutItem` or `UpdateItem` operations. It inspects an instance of `amano.Item` 
subclass to identify its state and generates an update expression if needed.

On the other hand, the `Put` method always executes `PutItem` expression. 
It does not take into consideration any context of the passed item.

Both `put` and `save` methods allow using conditional expressions.

```python
import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

forum_table = Table[Forum](client, table_name="Forum")
forum_table.put(Forum(ForumName="Amano Forum", Category="Amazon DynamoDB"))
```

### Retrieving data by a primary key

Dynamodb allows to choose between two types of primary key:
- __Partition key__. It is a simplified primary key. This means there 
should be no two items in a table with the same partition key value.
- __Composite key__. It is a combination of partition key and sort key. 
This means there might be items in a table with the same partition key, but they
must have different sort key values.


#### Retrieving by a partition key
```python
import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

forum_table = Table[Forum](client, table_name="Forum")

forum_table.get("Amazon DynamoDB")
```

#### Retrieving data by a composite key

```python
import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

class Thread(Item):
    ForumName: str
    Subject: str
    Message: str
    LastPostedBy: str
    Replies: int = 0
    Views: int = 0

forum_table = Table[Thread](client, table_name="Thread")

forum_table.get("Amazon DynamoDB", "Tagging tables")
```

#### Ensuring consistency reads

`consistent` parameter can be used to request a consistent read from a dynamodb
table.

### Querying a table




### Mapping item's fields

Usually schema of persisted data is different from its memory representation.
Amano provides a powerful mapping mechanism to cover this scenario. Mapping is
an operation which associates each element from one set of data 
(in-memory representation) to one or more elements of another set of data 
(dynamodb table).

```python
import boto3
from amano import Table, Item, Mapping

client = boto3.client("dynamodb")

class Forum(Item, mapping=Mapping.PASCAL_CASE):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0

forum_table = Table[Forum](client, table_name="Forum")
```

The above example will use built-in mapping strategy, which expects table's 
field names to follow PascalCase convention, and it will map them to standard 
python's snake case.

The following is the list of available mapping strategies:
- `Mapping.PASS_THROUGH`
- `Mapping.PASCAL_CASE`
- `Mapping.CAMEL_CASE`
- `Mapping.HYPHENS`

The `mapping` argument can also accept any `Dict[str, str]`. 
The dict keys should correspond to class attributes and its values 
to table's field names. Please see the example below:

```python
import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

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
```

# Item class internals

By default, a subclass of `amano.Item` behaves a bit like a dataclass, which 
means that initializer for the class is able to set class' properties.
Consider the following example:

```python
dynamodb_forum = Forum(
    name="Amazon DynamoDB",
    category="Amazon Web Services"
)

assert dynamodb_forum.name == "Amazon DynamoDB"
assert dynamodb_forum.threads == 0
```

`amano.Item` provides also an API, that helps to serialize and deserialize data.
A `hydrate` method can be used to deserialize data coming from database into an
item representation. A `extract` method can be used to store in-memory item 
representation to a database representation.

