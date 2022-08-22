class AmanoDBError(Exception):
    ...


class ItemNotFoundError(AmanoDBError):
    def __init__(self, message: str, query):
        self.query = query
        super().__init__(message)


class QueryError(AmanoDBError):
    ...
