# Amano DB

AWS DynamoDB Abstraction Layer built on Table Data Gateway Pattern.

## Features

 - Hydration and extraction of table items
 - Simple query mechanism with elegant abstraction
 - Interface for easy storing and retrieving data
 - Intelligent algorithm that saves DynamoDB's quota and money

## What is Amano?

As mentioned above, Amano is a Table Data Gateway Patter implementation, which relies on a table's already existing schema. It can understand existing schema to simplify daily tasks like; storing, retrieving and querying data.

Amano has a built-in index auto-use mechanism when performing a query. If there is an index, it will automatically pick the best matching index for the query.

## Basic Usage
The following examples rely on [AWS Discussion Forum Data Model](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SampleData.CreateTables.html#SampleData.CreateTables2).

### Defining your first Item

The example below defines a `Forum` class, which represents a record in a Dynamodb table. This class is required to instantiate parametrised `Table` class that abstracts access to Dynamodb's table.

> Please note that property names in the following example do not follow the PEP standards. The reason is that those names correspond to field names present in Dynamodb's Item. To fix this issue, please look into a [mapping section](#mapping-items-fields).

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

> Please note: `Forum` class extends `amano.Item` class. This is required by `amano.Table` to work properly. All the table's information, including; indexes, fields, projections, etc., are handled automatically and do not require any work on the developer's side.


### Storing Item in a table

To store Item, you can use the `put` or `save` method of `amano.Table` class.
The difference between those two methods is that `save` can understand state of the Item and can execute either `PutItem` or `UpdateItem` operation depending on the scenario. 

On the other hand, the `Put` method always executes `PutItem` expression. Which creates or fully overrides existing Item in case where no condition is provided.

> Both `put` and `save` methods allow using conditional expressions.

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

### Updating item in a table

`Table.update` edits an existing item's attributes. The difference between `put` and `update` is that update calculates Item's changes and performs a query only for the attributes that were changed. To update an Item, it must be retrieved first.

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
amano_forum = forum_table.get("Amano Forum")
amano_forum.Category = "Other Category"

assert forum_table.update(amano_forum)
```

### Deleting item from a table


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

# get an item
item = forum_table.get("Amano Forum", "Amazon DynamoDB")

# delete it
forum_table.delete(item)
```

### Conditional writes

`Put`, `update`, `save` and `delete` can perform conditional expressions (update Item only if given attribute exists, or when it asserts against given value). Amano provides abstraction which is built on the top of python's comparison operators (`==`, `=!`, `>`, `>=` `<`, `<=`) and bitwise operators (`&` - and, `|` - or).

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
amano_forum = forum_table.get("Amano Forum")
amano_forum.Category = "Other Category"

# Update forum only if there are no messages
assert forum_table.update(amano_forum, Forum.Messages == 0)
```

The above example shows how to update an Item in a certain situation. More complex conditions can be used, to learn more head to [Supported Conditions Section](#supported-conditions).

### Retrieving data by a primary key

Dynamodb allows to choose between two types of primary keys:
- __Partition key__. It is a simplified primary key. It means there 
should be no two items in a table with the same partition key value.
- __Composite key__. It is a combination of the partition key and sort key. 
This means there might be items in a table with the same partition key, but they must have different sort key values.


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

Both `query` and `get` methods of the `Table` class are supporting strongly consistent reads. To use strongly consistent reads, set `consistent_read` parameter to `True`:

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

forum_table.get("Amazon DynamoDB", "Tagging tables", consistent_read=True)
```


> To learn more about Dynamodb's read consistency click [here](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)


### Querying a table

Use the `key_condition` attribute to specify search criteria. A key condition is a condition that is executed against all items within a specific index. Amano can determine which index to use by looking at the fields in your key condition and table schema. If the corresponding index cannot be determined, the `query` method will throw an exception, and no actual request will be made to the table. Amano does all of this behind the scenes to save Dynamodb's quota.


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

result = forum_table.query(
    key_condition=(Thread.ForumName == "Amazon DynamoDB")
)
```

The above query will look for all items in the `Thread` table, where `ForumName` equals `Amazon DynamoDB`. Because the `Thread` table specifies the sort key (`Subject`), a search might be refined by using it in the `key_condition`. 

The sort key condition must use one of the following comparison operators:
 - equals `==`
 - greater than `>`
 - greater or equals `>=`
 - lower than `<`
 - lower or equals `<=`
 - between `field.between(a, b)`

### Supported conditions

Amano supports all the conditions of Dynamodb and provides an elegant abstraction, which simplifies querying and filtering Dynamodb tables.

> This guide uses the following symbols to provide a comprehensive list of examples:
> 
> __`{value}`__ is used to reference any valid value you may use in a condition.
>
> __`Item.field_{type}`__ is used to reference to a __class__' property, e.g.:`Item.field_int` may represent any valid class' property of an integer type.

#### `Item.field_any == {value}`

Matches all items in a table where `field_any` field's value is equal to a `{value}`.

> `{value}` can be of any supported type.

#### `Item.field_numeric < {value}`

Matches all items in a table where `field_numeric` field's value is lower than `{value}`.

> `{value}` should be a numeric or a string.

#### `Item.field_numeric <= {value}`

Matches all items in a table where `field_numeric` field's value is lower or equal to `{value}`.

> `{value}` should be a numeric or a string.

#### `Item.field_numeric > {value}`

Matches all items in a table where `field_numeric` field's value is greater than `{value}`.

> `{value}` should be a numeric or a string.

#### `Item.field_numeric >= {value}`

Matches all items in a table where `field_numeric` field's value is lower or equal to `{value}`.

> `{value}` should be a numeric or a string.

#### `Item.field_numeric.between({value_a}, {value_b})`

Matches all items in a table where `field_numeric` field's value is greater than or equals `{value_a}` and lower than or equals to `{value_b}`.

> `{value}` should be a numeric or a string.

#### `Item.field_str.begins_with({value})`

Matches all items in a table where `field_str` field's value starts with a `{value}`. This operation is __case-sensitive__.

> `{value}` should be a string.

### Working with `amano.Cursor`

The result of a query is always an instance of `amano.Cursor`. Cursor can be used to fetch all the records simply by iterating through it or by calling the `fetch` method.

```python

```


### Improved type hints

In order to get better type support in mypy and your IDE it is recommended 
to use `amano.Attribute` class when defining Item's attributes. 
Consider the following example which is redefining the `Thread` class:

```python
from amano import Item, Attribute

class Thread(Item):
    ForumName: Attribute[str]
    Subject: Attribute[str]
    Message: Attribute[str]
    LastPostedBy: Attribute[str]
    Replies: Attribute[int] = 0
    Views: Attribute[int] = 0
```

### Mapping item's fields

Usually, schema of persisted data is different from its memory representation.
Amano provides a powerful mapping mechanism to cover this scenario. Mapping is an operation which associates each element from one set of data (in-memory representation) to one or more elements of another set of data (Dynamodb table).

```python
import boto3
from amano import Table, Item, AttributeMapping

client = boto3.client("dynamodb")


class Forum(Item, mapping=AttributeMapping.PASCAL_CASE):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0


forum_table = Table[Forum](client, table_name="Forum")
```

The above example will use a built-in mapping strategy, which expects table's field names to follow PascalCase convention, and it will map them to standard python's snake case.

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

By default, a subclass of `amano.Item` behaves a bit like a dataclass, which means that the class's initialiser can set class' properties.

Consider the following example:

```python
dynamodb_forum = Forum(
    name="Amazon DynamoDB",
    category="Amazon Web Services"
)

assert dynamodb_forum.name == "Amazon DynamoDB"
assert dynamodb_forum.threads == 0
```

`amano.Item` also provides an API that helps to serialise and deserialise data. An `extract` method can be used to store in-memory item representation to a table representation. A `hydrate` method can be used to deserialise data coming from a table into an item representation.
