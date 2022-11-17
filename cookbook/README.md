# Cookbook

Welcome to the cookbook!

Before browsing through the examples, it is recommended to setup a local instance of DynamoDB. You can do this by simply running `docker-compose up` in the current directory.

> All the examples in this directory should work as they are. 

## Working with table's schema

[Creating and destroying a table](schema_example.py)

This example shows how to create a `Forum` table with two named indexes;
- global secondary index named `GSI`
- local secondary index named `LSI`

> This functionality should be primarily used for mockups and tests.

## Storing items in a table

[Put Item Example](put_example.py)

In this example `ReplyItem` is being instantiated and stored it in the `Reply` table using `put` method.

[Conditional Put Item Example](put_example.py)

## Working with a cursor

[Using cursor](cursor_example.py)
