Usually, schema of persisted data is different from its memory representation.
Amano provides a powerful mapping mechanism to cover this scenario. Mapping is an operation which associates each element from one set of data (in-memory representation) to one or more elements of another set of data (Dynamodb table).

--8<-- "docs/cookbook_header.md"

## Mapping with pre-build strategies

```python title="Mapping from PascalCase"
--8<-- "docs/examples/item_mapping_build_in.py"
```

The above example will use a built-in mapping strategy, which expects table's field names to follow PascalCase convention, and it will map them to standard python's snake case.

The following is the list of available mapping strategies:

- `Mapping.PASS_THROUGH`
- `Mapping.PASCAL_CASE`
- `Mapping.CAMEL_CASE`
- `Mapping.HYPHENS`

## Mapping with custom schema

The `mapping` argument can also accept any `Dict[str, str]`. 
The dict keys should correspond to class attributes and its values 
to table's field names. Please see the example below:

```python title="Mapping using custom schema"
--8<-- "docs/examples/item_mapping_custom_schema.py"
```
