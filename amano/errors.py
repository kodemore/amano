from __future__ import annotations

from typing import Any, Dict

from .condition import Condition
from .item import Item


class AmanoDBError(Exception):
    @classmethod
    def for_client_error(cls, message: str) -> AmanoDBError:
        return cls(f"Dynamodb client has failed with message: {message}.")


class QueryError(AmanoDBError):
    @classmethod
    def for_invalid_key_condition(
        cls, condition: Condition, reason: str = ""
    ) -> QueryError:
        return cls(f"Key condition `{condition}` is invalid. {reason}")

    @classmethod
    def for_invalid_index(
        cls, index: str, condition: Condition = None
    ) -> QueryError:
        if condition:
            return cls(
                f"Used unknown or invalid index `{index}` "
                f"for key condition `{condition}`"
            )

        return cls(f"Used unknown or invalid index `{index}` in query.")


class ReadError(AmanoDBError):
    pass


class WriteError(AmanoDBError):
    pass


class ItemNotFoundError(ReadError):
    def __init__(self, message: str, query: Dict[str, Any]):
        self.query = query
        super().__init__(message)


class PutItemError(WriteError):
    @classmethod
    def for_validation_error(cls, item: Item, message: str) -> PutItemError:
        return cls(
            f"Could not validate item {item}. "
            f"Validation failed with message: {message}"
        )


class UpdateItemError(WriteError):
    @classmethod
    def for_new_item(cls, item: Item) -> UpdateItemError:
        return cls(f"Could not update new item {item}.")


class DeleteItemError(WriteError):
    @classmethod
    def for_validation_error(cls, item: Item, message: str) -> DeleteItemError:
        return cls(
            f"Could not validate item {item}. "
            f"Validation failed with message: {message}"
        )
