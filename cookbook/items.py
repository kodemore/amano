from dataclasses import dataclass
from datetime import datetime
from typing import List

from amano import Item, AttributeMapping


@dataclass
class ForumItem(Item, mapping=AttributeMapping.PASCAL_CASE):
    name: str
    category: str
    threads: int
    messages: int
    views: int


@dataclass
class ThreadItem(Item, mapping=AttributeMapping.PASCAL_CASE):
    forum_name: str
    subject: str
    message: str
    last_posted_by: str
    last_posted_date_time: datetime
    views: int
    replies: int
    answered: int
    tags: List[str]


@dataclass
class ReplyItem(Item, mapping=AttributeMapping.PASCAL_CASE):
    id: str
    reply_date_time: datetime
    message: str
    posted_by: str

