from typing import Any, Callable, Dict, Generic, Iterator, List, Type, Union

from .base_attribute import AttributeValue
from .errors import QueryError
from .item import I


class Cursor(Generic[I]):
    def __init__(
        self, item_class: Type[I], query: Dict[str, Any], executor: Callable
    ):
        self._executor = executor
        self._query = query
        self.hydrate = True
        self._item_class = item_class
        self._fetched_records: List[Dict[str, AttributeValue]] = []
        self._current_index = 0
        self._exhausted = False
        self._last_evaluated_key: Dict[str, AttributeValue] = {}
        self._consumed_capacity: float = 0

    def __iter__(self) -> Iterator[Union[I, Dict[str, Any]]]:
        self._fetch()
        items_count = len(self._fetched_records)
        while self._current_index < items_count:
            item_data = self._fetched_records[self._current_index]
            if self.hydrate:
                yield self._item_class.hydrate(item_data)  # type: ignore
            else:
                yield item_data

            self._current_index += 1

            if (
                self._query.get("Limit")
                and self._current_index == self._query["Limit"]
            ):
                break

            if self._current_index >= items_count and not self._exhausted:
                self._fetch()
                items_count = len(self._fetched_records)

    def fetch(self, limit=0) -> List[Union[Dict[str, Any], I]]:
        self._current_index = 0
        fetched_items = []
        fetched_length = 0
        for item in self:
            fetched_items.append(item)
            fetched_length += 1
            if limit and fetched_length >= limit:
                break

        self._current_index = 0
        return fetched_items

    def _fetch(self) -> None:
        try:
            result = self._executor(**self._query)
            self._consumed_capacity = result["ConsumedCapacity"]["Table"][
                "CapacityUnits"
            ]
        except Exception as e:
            self._fetched_records = []
            self._exhausted = True
            raise QueryError(
                f"Could not execute query "
                f"`{self._query['KeyConditionExpression']}`, reason: {e}"
            )
        if "LastEvaluatedKey" in result:
            self._last_evaluated_key = result["LastEvaluatedKey"]
            self._query["ExclusiveStartKey"] = result["LastEvaluatedKey"]
        else:
            self._exhausted = True

        self._fetched_records = self._fetched_records + result["Items"]

    def count(self) -> int:
        count = len([item for item in self])
        self._current_index = 0
        self._fetched_records = []
        self._last_evaluated_key = {}
        self._exhausted = False
        if "ExclusiveStartKey" in self._query:
            del self._query["ExclusiveStartKey"]
        return count

    @property
    def consumed_capacity(self) -> float:
        return self._consumed_capacity
