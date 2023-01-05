Both `query` and `get` methods of the `Table` class are supporting strongly consistent reads. To use strongly consistent reads, set `consistent_read` parameter to `True`:

```python
from dataclasses import dataclass

import boto3
from amano import Table, Item

client = boto3.client("dynamodb")

@dataclass
class Thread(Item):
    ForumName: str
    Subject: str
    Message: str
    LastPostedBy: str
    Replies: int = 0
    Views: int = 0

forum_table = Table[Thread](client, table_name="Thread")

forum_table.get("Amazon DynamoDB", "Tagging tables", consistent_read=True)
```


> To learn more about Dynamodb's read consistency click [here](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)
