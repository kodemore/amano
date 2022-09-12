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
Following examples relies on [AWS Discussion Forum Data Model](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SampleData.CreateTables.html#SampleData.CreateTables2).

### Defining your Forum Item

The example below defines an item that represents a record in dynamo database,
and instantiates new table object which provides abstraction layer around 
table operations:


```python
import boto3
from amano import Table, Item, Attribute

class Forum(Item, mapping={
    "name": "ForumName",
    "category": "Category",
    "threads": "Threads",
    "messages": "Messages",
    "views": "Views"
}):
    name: Attribute[str]
    category: Attribute[str]
    threads: Attribute[int] = 0
    messages: Attribute[int] = 0
    views: Attribute[int] = 0


client = boto3.client("dynamodb")
forum_table = Table[Forum](client, table_name="Forum")
```

`Forum` is a representation of an `Item` thus it has to extend `amano.Item` class.
`Item` provides a mapping functionality, so you can separate in-memory 
representation from your database representation. 

### Storing item in a table

```python
item = Forum(name="Amano Forum", category="Amazon DynamoDB") 
forum_table.save(item)
```

### Retrieving data by primary key

```python
forum_table.get("Amano Forum", consistent=False)
```

`consistent` parameter can be used to request a consistent read from a dynamodb
table.

### Quering a table

#### Quering by pk

```python
cursor = forum_table.query(Forum.name == "Amano Forum")

for item in cursor:
    assert isinstance(item, Forum)
```


`consistent` parameter can be used to request a consistent read from a dynamodb
table.

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

