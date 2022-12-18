# Querying a table

To query a table you have to first instantiate `amano.Table` generic class, and execute a query method and pass a search criteria through `key_condition` argument. Difference in interface between `amano` and `boto` libraries is the requirement of specifying an index and the construction of query itself. Amano is using more flexible and approachable solution.

> Amano can determine which index to use by looking at the fields in your key condition and the table's schema. If a corresponding index cannot be determined, the `query` method will throw an exception, and no actual request will be made to the table. Amano does all of this behind the scenes to save Dynamodb's quota.


### Performing a query

```python  title="Query a table"
--8<-- "docs/examples/table_query.py"
```

> The above query will look for all items in the `Thread` table, where `ForumName` equals `Amazon DynamoDB`. Because the `Thread` table specifies the sort key (`Subject`), a search might be refined by using it in the `key_condition`.

### Comparison operators

Amano supports all the conditions of Dynamodb and provides an elegant abstraction, which simplifies querying and filtering Dynamodb tables.

> This guide uses the following symbols to provide a comprehensive list of examples:
> 
> __`{value}`__ is used to reference any valid value you may use in a condition.
>
> __`Item.field_{type}`__ is used to reference to a __class__' property, e.g.:`Item.field_int` may represent any valid class' property of an integer type.

#### Equals

```title="Expression structure"
Item.field_any == {value}
```

Matches all items in a table where `field_any` field's value is equal to a `{value}`.

> `{value}` can be of any supported type.

#### Lower than

```title="Expression structure"
Item.field_numeric < {value}
```

Matches all items in a table where `field_numeric` field's value is lower than `{value}`.

> `{value}` should be a numeric or a string.

#### Lower or equal

```
Item.field_numeric <= {value}
```

Matches all items in a table where `field_numeric` field's value is lower or equal to `{value}`.

> `{value}` should be a numeric or a string.

#### Greater than

```title="Expression structure"
Item.field_numeric > {value}
```

Matches all items in a table where `field_numeric` field's value is greater than `{value}`.

> `{value}` should be a numeric or a string.

#### Greater or equal

```title="Expression structure"
Item.field_numeric >= {value}
```

Matches all items in a table where `field_numeric` field's value is lower or equal to `{value}`.

> `{value}` should be a numeric or a string.

#### Between

```title="Expression structure"
Item.field_numeric.between({value_a}, {value_b})
```

Matches all items in a table where `field_numeric` field's value is greater than or equals `{value_a}` and lower than or equals to `{value_b}`.

> `{value}` should be a numeric or a string.

#### Begins with

```title="Expression structure"
Item.field_str.begins_with({value})
```

Matches all items in a table where `field_str` field's value starts with a `{value}`. This operation is __case-sensitive__.

> `{value}` should be a string.

#### Sort key comparison operators

The sort key has a specific functionality in DynamoDB, thus it supports only limited amount of comparison operators:

 - equals `==`
 - greater than `>`
 - greater or equals `>=`
 - lower than `<`
 - lower or equals `<=`
 - between `field.between(a, b)`
