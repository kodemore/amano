# Advanced features of the Item class

> Features described in this section are used internally by the library and its components. It is not required to familiarise yourself with  them in order to effectively use the library.

Each change in the instance of the `amano.Item` subclass is recorded and stored in a memory. 

The following guide can help you to understand how you can use these features in your applications.

## Getting item state

An Item can be in one of the following three states:

- `new`
- `clean`
- `dirty`

A `new` state means that object has been just instantiated and no properties were modified.

A `clean` state means that object has been modified, and it is synchronized with its database representation.

A `dirty` state means that object has been modified, and it is not synchronized with its database representation.

The following code example shows state changes of an object:

```python title="Getting item's state"
--8<-- "docs/examples/item_states.py"
```

> Note: to set item back to a `clean` state you have to commit its changes.


## Committing the changes

```python title="Commiting item's changes"
--8<-- "docs/examples/item_commit.py"
```


> Note: that `commit` function just creates a commit info inside the item instance. This means it is not persisted in the database, even if you use an `amano.Table.update` or `amano.Table.save`, the item will be in the `clean` state and won't be updated.


## Generating diff for an item

A diff is a tuple containing two values. First value is a string representation of an update query (when performed it will synchronise the item with its database representation). The second value is a key-value object used to interpolate the query string.

```python title="Generating item's diff"
--8<-- "docs/examples/item_diff.py"
```
