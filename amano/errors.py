from typing import Any, Dict


class AmanoDBError(Exception):
    ...


class ItemNotFoundError(AmanoDBError):
    def __init__(self, message: str, query: Dict[str, Any]):
        self.query = query
        super().__init__(message)


class QueryError(AmanoDBError):
    ...


class PutItemError(QueryError):
    ...
