# Retrieving items from a table

There are two ways to retrieve your data from DynamoDB's table:

 - by querying a table _`(amano.Table.query)`_
 - by scanning a table _`(amano.Table.scan)`_

Differences between those two operations are in performance, cost and flexibility. Generally speaking you should always favour query over scan. 

To query a table you have to first instantiate `amano.Table` generic class, and execute a query method and pass a search criteria through `key_condition` argument. Difference in interface between `amano` and `boto` libraries is the requirement of specifying an index and the construction of query itself. Amano is using more flexible and approachable solution.

> Amano can determine which index to use by looking at the fields in your key condition and the table's schema. If a corresponding index cannot be determined, the `query` method will throw an exception, and no actual request will be made to the table. Amano does all of this behind the scenes to save Dynamodb's quota.


### Query operation

```python  title="Query a table"
--8<-- "docs/examples/table_query.py"
```

> The above query will look for all items in the `Thread` table, where `ForumName` equals `Amazon DynamoDB`. Because the `Thread` table specifies the sort key (`Subject`), a search might be refined by using it in the `key_condition`.

#### Query with a filter condition

A filter condition enables you to further refine the query results. Filter condition is applied after a query. Therefore, a query consumes the same amount of read capacity.

A filter condition cannot contain a partition key or a sort key, use a key condition instead for those attributes.

A filter condition and key condition use the same mechanism, but filter condition uses wider range of operators.

The following example shows how to use filter condition in an example query:

```python  title="Query with a filter condition"
--8<-- "docs/examples/table_query_with_filter.py"
```

### Scan operation

Scan operations are very flexible as they can be run without prior index setup.

When a scan operation is executed every item in a given table is being read, which as you can imagine is a heavy and costly operation. Thus scans operations should be used as a last bastion or in a specific scenarios.

```python  title="Scan a table"
--8<-- "docs/examples/table_scan.py"
```

## Working with cursor

Scan and query operations as a result are returning a cursor. Cursor is an iterator object which can be used to access items from your DynamoDB table. The simplest use case is to iterate through the cursor until it is exhausted, like in the example below:

```python title="Cursor a basic usage"
--8<-- "docs/examples/cursor_basic_usage.py"
```

### Fetching items

When iteration through all the results is not an option you can just fetch desired amount of items from a table by using the `fetch` method on a cursor object.

```python title="Fetching items"
--8<-- "docs/examples/cursor_fetch.py"
```

The `fetch` method will try to retrieve the desired amount of items matching the search criteria from a table. If there are not enough items in the search result, the `fetch` method will return all items from the result. 

### Counting items

To understand how many items have matched the search criteria you can use the `count` method of a cursor.

```python title="Counting items"
--8<-- "docs/examples/cursor_count.py"
```

!!! warning
    The `count` method will retrieve all the items matching the search results and store them in the memory. Despite the fact that this can be the only option to understand the size of your result set, it should be used with care. 
