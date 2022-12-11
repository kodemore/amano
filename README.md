# Amano DB

AWS DynamoDB Abstraction Layer built on Table Data Gateway Pattern.

## Features

 - Hydration and extraction of table items
 - Simple query mechanism with elegant abstraction
 - Interface for easy storing and retrieving data
 - Intelligent algorithm that saves DynamoDB's quota and money

## What is Amano?

As mentioned above, Amano is a Table Data Gateway Pattern implementation, which relies on a table's already existing schema. It can understand existing schema to simplify daily tasks like; storing, retrieving and querying data.

Amano has a built-in index auto-use mechanism when performing a query. If there is an index, it will automatically pick the best matching index for the query.

## Docs

### Conditional writes

`Put`, `update`, `save` and `delete` can perform conditional expressions (update Item only if given attribute exists, or when it asserts against given value). Amano provides abstraction which is built on the top of python's comparison operators (`==`, `=!`, `>`, `>=` `<`, `<=`) and bitwise operators (`&` - and, `|` - or).

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

# Update forum only if there are no messages
assert forum_table.update(amano_forum, Forum.Messages == 0)
```

The above example shows how to update an Item in a certain situation. More complex conditions can be used, to learn more head to [Supported Conditions Section](#supported-conditions).


#### Ensuring consistency reads

Both `query` and `get` methods of the `Table` class are supporting strongly consistent reads. To use strongly consistent reads, set `consistent_read` parameter to `True`:

```python
from dataclasses import dataclass

import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

@dataclass
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
from dataclasses import dataclass

import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

@dataclass
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

The result of a query or scan is always an instance of `amano.Cursor`. Cursors can be used to fetch all the records simply by iterating through them or by calling provided `fetch` method:

```python
from amano import Item, AttributeMapping
import boto3

client = boto3.client("dynamodb")


class Forum(Item, mapping=AttributeMapping.PASCAL_CASE):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0

```

### Improved type hints

In order to get better type support in mypy and your IDE it is recommended 
to use `amano.Attribute` class when defining Item's attributes. 
Consider the following example which is redefining the `Thread` class:

```python
from dataclasses import dataclass

from amano import Item, Attribute

@dataclass
class Thread(Item):
    ForumName: Attribute[str]
    Subject: Attribute[str]
    Message: Attribute[str]
    LastPostedBy: Attribute[str]
    Replies: Attribute[int] = 0
    Views: Attribute[int] = 0
```

# Item class internals

`amano.Item` changes the default class behaviour for an object's attributes. It does it to catch all changes inside any instance of `amano.Item` class. Each change creates a changelog for a given instance, which is later used to generate an update expression. 
The changelog is stored in the `__log__` attribute. 

Additionally, `amano` inspects class attributes to generate a schema that later on is used to perform various queries and auto-index selection. Generated schema is stored in the `__schema__` attribute. 

To utilise potential the above behaviours, the library provides following interface:

- `amano.item.commit(item: Item)`
- `amano.item.hydrate(what: Type[I], value: dict)`
- `amano.item.extract(item: Item)`
- `amano.item.from_dict(what: Type[I], value:dict)`
- `amano.item.as_dict(value: Item)`

## `amano.item.commit`
Creates new commit from changes kept in `__log__` attribute. 

## `amano.item.hydrate`
Create new instance of the `Item` class from DynamoDB item representation.

## `amano.item.extract`
Creates a DynamoDB item representation from an instance of Item.

## `amano.item.from_dict`
Creates new instance of the `Item` class from a dict representation.

## `amano.item.as_dict`
Creates a dict representation of an `Item` object.
