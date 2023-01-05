# Cookbook

If you prefer to read code by examples instead going through entire documentation, here is good news for you. This cookbook is a collection of all examples present in our entire documentation. Familiarising and understanding all the example below means you should be able to use most of the features provided by the Amano library.

## Item

### Definition

```python title="Basic example"
--8<-- "docs/examples/item_basic_definition.py"
```


```python title="Built-in item initializer"
--8<-- "docs/examples/item_initializer.py"
```

```python title="Dataclass example"
--8<-- "docs/examples/item_dataclass_definition.py"
```


### Instantiation
```python title="Basic instantiation"
--8<-- "docs/examples/item_basic_instantiate.py"
```

```python title="Instantiation from a dict"
--8<-- "docs/examples/item_from_dict_instantiation.py"
```

```python title="Instantiation from raw DynamoDB's data"
--8<-- "docs/examples/item_raw_instantiation.py"
```

### Serialisation

```python title="Serialisation item to dict"
--8<-- "docs/examples/item_serialisation.py"
```

```python title="Serialisation item to DynamoDB's format"
--8<-- "docs/examples/item_extraction.py"
```

### Mapping
```python title="Mapping from PascalCase"
--8<-- "docs/examples/item_mapping_build_in.py"
```

```python title="Mapping using custom schema"
--8<-- "docs/examples/item_mapping_custom_schema.py"
```

### Advanced features

```python title="Getting item's state"
--8<-- "docs/examples/item_states.py"
```

```python title="Commiting item's changes"
--8<-- "docs/examples/item_commit.py"
```

```python title="Generating item's diff"
--8<-- "docs/examples/item_diff.py"
```

## Table

### Item storage

```python title="Item storage using put method"
--8<-- "docs/examples/table_storing_items.py"
```

### Item retrieval

```python title="Get an item by a partition key"
--8<-- "docs/examples/table_get_by_partition_key.py"
```


```python title="Get an item by a partition key"
--8<-- "docs/examples/table_get_by_partition_key.py"
```

### Working with cursor

```python title="Cursor a basic usage"
--8<-- "docs/examples/cursor_basic_usage.py"
```

```python title="Fetching items"
--8<-- "docs/examples/cursor_fetch.py"
```

```python title="Counting items"
--8<-- "docs/examples/cursor_count.py"
```


### Item update

```python title="Update item"
--8<-- "docs/examples/table_basic_update.py"
```

### Item deletion

```python title="Delete item"
--8<-- "docs/examples/table_item_delete.py"
```

```python title="Delete item by PK"
--8<-- "docs/examples/table_item_delete_pk.py"
```

### Querying


```python  title="Query a table"
--8<-- "docs/examples/table_query.py"
```

```python  title="Query with a filter condition"
--8<-- "docs/examples/table_query_with_filter.py"
```
