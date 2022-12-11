# Basic Usage
--8<-- "docs/cookbook_header.md"

## Instantiation

From outside a subclass of the `amano.Item` class does not differ much from a normal class. You can instantiate it in the same way as a usual class; define an initializer and so on:

### Basic instantiation

```python title="Basic instantiation"
--8<-- "docs/examples/item_basic_instantiate.py"
```

### Instantiating from a dict

Any subclass of `amano.Item` can be instantiated with `amano.item.from_dict` function.

```python title="Instantiation using a dict"
--8<-- "docs/examples/item_from_dict_instantiation.py"
```

### DynamoDB raw item instantiation

You can also instantiate your item class using raw data coming directly from DynamoDB. 

```python title="Instantiation using data coming directly from DynamoDB"
--8<-- "docs/examples/item_raw_instantiation.py"
```

## Serialisation

### Basic serialisation

Any instance of `amano.Item` subclass can be easy transformed into dictionary:

```python title="Serialisation item to dict"
--8<-- "docs/examples/item_serialisation.py"
```

### Serialisation to DynamoDB's format

```python title="Serialisation item to DynamoDB's format"
--8<-- "docs/examples/item_extraction.py"
```
