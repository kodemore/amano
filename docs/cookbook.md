# Cookbook

If you prefer to read code by examples instead going through entire documentation, here is good news for you. This cookbook is a collection of all examples present in our entire documentation. Familiarising and understanding all the example below means you should be able to use most of the features provided by the Amano library.

## Item

### Definition

```python title="Basic example"
--8<-- "docs/examples/item_basic_definition.py"
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
