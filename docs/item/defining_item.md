# Defining Item

--8<-- "docs/cookbook_header.md"

The example below defines a `Forum` class, which represents a record in a DynamoDB's table. The `Forum` class is required to instantiate parametrised `amano.Table` class that abstracts access to Dynamodb's table.

> Please note that property names in the following example do not follow the PEP standards. The reason is that those names correspond to field names present in Dynamodb's Item. To fix this issue, please look into a [Mapping Section](/field_mapping).
 
## Basic item definition

```python title="Basic Item Example"
--8<-- "docs/examples/item_basic_definition.py"
```

> Please note: `Forum` class extends `amano.Item` class. This is required by `amano.Table` to work properly. All the table's information, including; indexes, fields, projections, etc., are handled automatically and do not require any work on the developer's side.

## Built-in initializer

By default, if there is no initializer specified for `amano.Item` subclass, it will behave like a dataclass. This means you can just instantiate a class with its properties like in the example below:

```python title="Built-in item initializer"
--8<-- "docs/examples/item_initializer.py"
```


## Dataclass integration

Any subclass of `amano.Item` can be used with dataclasses python's package.

```python title="Dataclass integration"
--8<-- "docs/examples/item_dataclass_definition.py"
```
