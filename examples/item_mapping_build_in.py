from amano import Item, AttributeMapping
from dataclasses import dataclass


@dataclass
class Forum(Item, mapping=AttributeMapping.PASCAL_CASE):
    forum_name: str
    category: str
    threads: int = 0
    messages: int = 0
    views: int = 0
