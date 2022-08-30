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

### Table schema

```json
{
  "TableName": "ecommerce",
  "KeySchema": [
    {
      "AttributeName": "user_id",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "sku",
      "KeyType": "RANGE"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "user_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "sku",
      "AttributeType": "S"
    }
  ],
  "LocalSecondaryIndexes": [
    {
      "IndexName": "LocalArtistAndAlbumNameIndex",
      "KeySchema": [
        {
          "AttributeName": "artist_name",
          "KeyType": "HASH"
        },
        {
          "AttributeName": "album_name",
          "KeyType": "RANGE"
        }
      ],
      "Projection": {
        "ProjectionType": "ALL"
      }
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "GlobalAlbumAndTrackNameIndex",
      "KeySchema": [
        {
          "AttributeName": "album_name",
          "KeyType": "HASH"
        },
        {
          "AttributeName": "track_name",
          "KeyType": "RANGE"
        }
      ],
      "Projection": {
        "ProjectionType": "ALL"
      }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
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

