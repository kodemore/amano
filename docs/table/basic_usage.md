# Basic Usage

--8<-- "docs/examples_header.md"


## Item storage

To store Item, you can use the `put` or `save` method of `amano.Table` class.
The difference between those two methods is that `save` can understand state of the Item and can execute either `PutItem` or `UpdateItem` operation depending on the scenario. 

On the other hand, the `Put` method always executes `PutItem` expression. Which creates or fully overrides existing Item in case where no condition is provided.

> Both `put` and `save` methods allow using conditional expressions.

```python title="Using put method"
--8<-- "docs/examples/table_storing_items.py"
```


## Item retrieval

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

If your table defines composite key (key composed of a partition key and a sort key), you must provide both values in the get method, like below:

```python title="Retrieve by a composite key"
--8<-- "docs/examples/table_get_by_composite_key.py"
```

## Item update

`Table.update` edits an existing item's attributes. The difference between `put` and `update` is that update calculates Item's changes and performs a query only for the attributes that were changed. To update an Item, it must be retrieved first.

```python title="Udpdate item"
--8<-- "docs/examples/table_basic_update.py"
```

## Item deletion

DynamoDB identifies each item by a primary key. In order to delete an item you have to identify it first. In Amano identification is done by retrieval, like in the example below:

```python title="Delete item"
--8<-- "docs/examples/table_item_delete.py"
```

If you know the primary key upfront you can simply delete an item without retrieving it. Please consider the following example:

```python title="Delete item by PK"
--8<-- "docs/examples/table_item_delete_pk.py"
```
