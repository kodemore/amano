# Comparison operators and functions

Amano supports all the comparison operators and functions of Dynamodb and provides an elegant abstraction around them, which simplifies querying and filtering Dynamodb tables.

!!! note "About this guide"
    This guide uses the following symbols to provide a comprehensive list of examples:
    
     - __`{value: type}`__ is used to reference any valid value you may use in a condition of a given type. If no `type` is specified it applies to all types.
     - __`Item`__ is used to reference to an item class
     - __`{attribute: type}`__ is used to reference to an attribute of an item class of a given type `type`. If no `type` is specified it applies to all types.

## Comparison operators

### Equals

Matches all items in a table where `{attribute}`'s value is equal to a `{value}`.

=== "Structure"
    ```
    Item.{attribute} == {value}
    ```
=== "Example"
    ```
    User.name == "Bob"
    ```


### Lower than

Matches all items in a table where `{attribute}`'s value is lower than a `{value}`.

=== "Structure"
    ```
    Item.{attribute: numeric} < {value: numeric}
    ```
=== "Example"
    ```
    User.age < 130
    ```


### Lower or equal

Matches all items in a table where `{attribute}`'s value is lower or equal to a `{value}`.

=== "Structure"
    ```
    Item.{attribute: numeric} <= {value: numeric}
    ```
=== "Example"
    ```
    Wallet.value <= 10.5
    ```


### Greater than

Matches all items in a table where `{attribute}`'s value is greater than  a `{value}`.

=== "Structure"
    ```
    Item.{attribute: numeric} > {value: numeric}
    ```
=== "Example"
    ```
    Wallet.value > 0.1
    ```

### Greater or equal

Matches all items in a table where `{attribute}`'s value is lower or equal to a `{value}`.

=== "Structure"
    ```
    Item.{attribute: numeric} >= {value: numeric}
    ```
=== "Example"
    ```
    User.age >= 18
    ```

### Between

Matches all items in a table where `{attribute}`'s value is greater than or equals to `{value_a}` and lower than or equals to `{value_b}`.

=== "Structure"
    ```
    Item.{attribute: numeric}.between({value_a: numeric}, {value_b: numeric})
    ```
=== "Example"
    ```
    User.age.between(18, 120)
    ```

## Functions

### (Not) Exists

Matches all items in a table where `{attribute}` is (not) defined in the given item.

=== "Structure"
    ```
    Item.{attribute}.exists()
    Item.{attribute}.not_exists()
    ```
=== "Example"
    ```
    User.age.exists()
    User.age.not_exists()
    ```

### Is Type

Matches all items in a table where `{attribute}` is of a given type.
Passed type must be an instance of `amano.AttributeType` class. Supported values are:

 - for string type - `amano.AttributeType.STRING` 
 - for numeric types - `amano.AttributeType.NUMBER`
 - for boolean type - `amano.AttributeType.BOOLEAN` 
 - for binary types - `amano.AttributeType.BINARY` 
 - for none type - `amano.AttributeType.NULL` 
 - for list types - `amano.AttributeType.LIST` 
 - for map types - `amano.AttributeType.MAP` 
 - for number set - `amano.AttributeType.NUMBER_SET` 
 - for string set - `amano.AttributeType.STRING_SET` 
 - for binary set - `amano.AttributeType.BINARY_SET` 
 - for any type - `amano.AttributeType.ANY` 

=== "Structure"
    ```
    Item.{attribute}.is_type({value: amano.AttributeType.NUMBER})
    ```
=== "Example"
    ```
    User.age.is_type(amano.AttributeType.NUMBER)
    ```

### Begins with

Matches all items in a table where `{attribute}` starts of a given string `{value}`. There is an alternate function called `startswith`, which can be used interchangeably.

=== "Structure"
    ```
    Item.{attribute}.begins_with({value: string})
    Item.{attribute}.startswith({value: string})
    ```
=== "Example"
    ```
    User.name.begins_with("I")
    User.name.startswith("I")
    ```

### Contains

Matches all items in a table where `{attribute}` contains a value `{value}`.

=== "Structure"
    ```
    Item.{attribute: list|set|string}.contains({value})
    ```
=== "Example"
    ```
    User.name.contains("a")
    User.favourites.contains("music")
    ```

### In

Matches all items in a table where `{attribute}`'s value is within a list of values `{value}`. When comparing size you can use any of comparison operators.

=== "Structure"
    ```
    Item.{attribute}.in({value})
    ```
=== "Example"
    ```
    User.country.in(["US", "UK"])
    ```

### Size

Matches all items in a table where `{attribute}` is sized or its size passes a comparison with a `{value}`. You can use all comparison operators except `between`. 

=== "Structure"
    ```
    Item.{attribute}.size()
    Item.{attribute}.size() > {value}
    ```
=== "Example"
    ```
    User.favourites.size()
    User.favourites.size() > 2
    ```


## Logical evaluations

Use the `and`, `or`, and `not` python's logical operators to perform logical evaluations in your queries. 

Because logical operations in python takes any precedence over comparison operations make sure to wrap comparison operations in parentheses. Otherwise, your query may result in an error. 

For example, this is valid:
```python
(User.favourites.size() > 1) and (User.favourites.size() < 20)
```

And the below will result in an error (as `1` and `User.favourites.size()` will be executed as an expression before the comparison):

```python
User.favourites.size() > 1 and User.favourites.size() < 20
```

You can also use additional parentheses (like you would normally do in python) to change the precedence of a logical evaluation.

## Sort key evaluation

The sort key has a specific functionality in DynamoDB, thus it supports only limited amount of operators

__Supported comparisons operators__

 - equals `==`
 - greater than `>`
 - greater or equals `>=`
 - lower than `<`
 - lower or equals `<=`
 - between `field.between(a, b)`

__Supported functions__
 
 - `begins_with` (aka `startswith`)
