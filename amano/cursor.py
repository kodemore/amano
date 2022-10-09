from typing import Any, Callable, Dict, Generic, Iterator, List, Type, Union

from .base_attribute import AttributeValue
from .errors import QueryError
from .item import I, hydrate


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
        self._current_index = 0
        if not self._fetched_records:
            self._fetch()

        items_count = len(self._fetched_records)
        while self._current_index < items_count:
            item_data = self._fetched_records[self._current_index]
            if self.hydrate:
                yield hydrate(self._item_class, item_data)  # type: ignore
            else:
                yield item_data

            self._current_index += 1

            if self._current_index >= items_count and not self._exhausted:
                self._fetch()
                items_count = len(self._fetched_records)

    def fetch(self, items=0) -> List[Union[Dict[str, Any], I]]:
        self._current_index = 0
        fetched_items = []
        fetched_length = 0
        for item in self:
            fetched_items.append(item)
            fetched_length += 1
            if items and fetched_length >= items:
                break

        self._current_index = 0
        return fetched_items

    def _fetch(self) -> None:
        if self._exhausted:
            return

        try:
            result = self._executor(**self._query)
            self._consumed_capacity = result["ConsumedCapacity"]["Table"][
                "CapacityUnits"
            ]
        except Exception as error:
            self._fetched_records = []
            self._exhausted = True
            raise QueryError.for_client_error(str(error)) from error
        if "LastEvaluatedKey" in result:
            self._last_evaluated_key = result["LastEvaluatedKey"]
            self._query["ExclusiveStartKey"] = result["LastEvaluatedKey"]
        else:
            self._exhausted = True

        self._fetched_records = self._fetched_records + result["Items"]

    def count(self) -> int:
        while not self._exhausted:
            self._fetch()

        return len(self._fetched_records)

    @property
    def consumed_capacity(self) -> float:
        return self._consumed_capacity
