It is not required but in order to get better type support in mypy and your IDE it is recommended 
to use `amano.Attribute` class when defining Item's attributes. 
Consider the following example which is redefining the `Thread` class:

```python
from dataclasses import dataclass

from amano import Item, Attribute

@dataclass
class Thread(Item):
    ForumName: Attribute[str]
    Subject: Attribute[str]
    Message: Attribute[str]
    LastPostedBy: Attribute[str]
    Replies: Attribute[int] = 0
    Views: Attribute[int] = 0
```
