`Put`, `update`, `save` and `delete` can perform conditional expressions (update Item only if given attribute exists, or when it asserts against given value). Amano provides abstraction which is built on the top of python's comparison operators (`==`, `=!`, `>`, `>=` `<`, `<=`) and bitwise operators (`&` - and, `|` - or).

```python
from dataclasses import dataclass

import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

@dataclass
class Forum(Item):
    ForumName: str
    Category: str
    Threads: int = 0
    Messages: int = 0
    Views: int = 0

forum_table = Table[Forum](client, table_name="Forum")
amano_forum = forum_table.get("Amano Forum")
amano_forum.Category = "Other Category"

# Update forum only if there are no messages
assert forum_table.update(amano_forum, Forum.Messages == 0)
```

The above example shows how to update an Item in a certain situation. More complex conditions can be used, to learn more head to [Supported Conditions Section](#supported-conditions).
