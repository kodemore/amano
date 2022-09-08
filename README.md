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

Examples below are using [this table schema](docs/example_schema.json)

```
┌──────────────────────────────────┬─────────┬────────────────────────┬────────────────┐
│      Primary Key         │       │
├───────────────┬──────────┼───────┼─────────┼────────────────────────┼────────────────┤
│ Partition key │ Sort Key │                          │ Value 2 │ 123                    │           10.0 │
├───────────────┼──────────┼
Separate                         │ cols    │ with a tab or 4 spaces │       -2,027.1 │
│ This is a row with only one cell │         │                        │                │
└──────────────────────────────────┴─────────┴────────────────────────┴────────────────┘
```

```python
from decimal import Decimal
import boto3
from amano import Table, Item


class CartItem(Item):
    user_id: str
    sku: str
    item_name: str
    price_value: Decimal
    quantity: int


client = boto3.client("dynamodb")
shopping_cart = Table[CartItem](client, table_name="ecommerce")

# put an item into a cart
pillow = CartItem(
    user_id="bob@work.it",
    sku="pillow#1",
    item_name="Blue Pillow",
    price_value=Decimal("10.00"),
    quantity=1
)
shopping_cart.put(pillow)

# retrieve item assuming your pk
```

# API

## Storing item in a table

