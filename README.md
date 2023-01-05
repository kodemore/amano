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
 
Documentation is available under [https://kodemore.github.io/amano/](https://kodemore.github.io/amano/).


## Basic Usage

```python
from amano import Table, Item
import boto3

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

