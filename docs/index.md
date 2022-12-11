# Amano DB

AWS DynamoDB Abstraction Layer.

## What is Amano?

Amano is a Table Data Gateway Pattern implementation, which means there are two objects:

 - a table, represented by `amano.Table`
 - an item, represented by `amano.Item`

A `Table` represents DynamoDB's table and acts as an access layer to a given table. An `Item` represents a single record in DynamoDB's table.

It can understand existing schema to simplify daily tasks like; storing, retrieving and querying data.

Amano has a built-in auto-index resolving mechanism, if there is an index, it will automatically pick the best matching index for the query. This should simplify your queries and decrease development time. 

## Features

 - Hydration and extraction of table items
 - Simple query mechanism with elegant abstraction
 - Interface for easy storing and retrieving data
 - Intelligent algorithm that saves DynamoDB's quota and money

