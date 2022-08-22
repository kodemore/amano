from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import Generic, TypeVar, Tuple, Union, Type, List, Any, Dict

from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.client import DynamoDBClient
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from mypy_boto3_dynamodb.service_resource import Table as DynamoDBTable
from .attribute import Attribute
from .errors import ItemNotFoundError, QueryError

from .item import Item

I = TypeVar("I", bound=Item)

_serialize_item = TypeSerializer().serialize
_deserialize_item = TypeDeserializer().deserialize


class KeyType(Enum):
    PARTITION_KEY = "HASH"
    SORT_KEY = "RANGE"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other

        return other == self


class IndexType(Enum):
    LOCAL_INDEX = "local_index"
    GLOBAL_INDEX = "global_index"
    PRIMARY_KEY = "primary_key"


class Cursor(Generic[I]):
    ...


class Index:
    def __init__(self, index_type: IndexType, name: str, partition_key: str, sort_key: str = ""):
        self.index_type = index_type
        self.name = name
        self.partition_key = partition_key
        self.sort_key = sort_key


def extract_indexes(index_list: List[Dict[str, Any]], index_type: IndexType) -> Dict[str, Index]:
    indexes = {}
    for index_data in index_list:
        if "IndexStatus" in index_data and index_data["IndexStatus"] != "ACTIVE":
            continue
        key_schema = index_data["KeySchema"]
        if len(key_schema) > 1:
            if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[0]["AttributeName"],
                    key_schema[1]["AttributeName"]
                )
            else:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[1]["AttributeName"],
                    key_schema[0]["AttributeName"]
                )
        else:
            index = Index(
                index_type,
                index_data["IndexName"],
                key_schema[0]["AttributeName"]
            )
        indexes[index.name] = index

    return indexes


class Table(Generic[I]):
    _PRIMARY_KEY_NAME = "#"
    __item_class__: Type[Item]

    def __init__(self, db_client: DynamoDBClient, table_name: str):
        if not self._item_class:
            raise SyntaxError(
                f"{self.__class__} must be parametrized with a subtype of {Item.__module__}.{Item.__qualname__}"
            )

        self._db_client = db_client
        self._table_name = table_name
        self._table_meta = {}
        self._fetch_table_meta(table_name)
        self._hydrate_indexes()
        self._validate_table_primary_key()

    def _fetch_table_meta(self, table_name):
        try:
            self._table_meta = self._db_client.describe_table(TableName=self._table_name)["Table"]
        except ClientError as e:
            raise ValueError(f"Table with name {table_name} was not found") from e
        except KeyError as e:
            raise ValueError(f"There was an error while retrieving `{table_name}` information.") from e

    def _hydrate_indexes(self):
        key_schema = self._table_meta.get("KeySchema")
        if len(key_schema) > 1:
            if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
                primary_key = Index(
                    IndexType.PRIMARY_KEY,
                    self._PRIMARY_KEY_NAME,
                    key_schema[0]["AttributeName"],
                    key_schema[1]["AttributeName"]
                )
            else:
                primary_key = Index(
                    IndexType.PRIMARY_KEY,
                    self._PRIMARY_KEY_NAME,
                    key_schema[1]["AttributeName"],
                    key_schema[0]["AttributeName"]
                )
        else:
            primary_key = Index(
                IndexType.PRIMARY_KEY,
                self._PRIMARY_KEY_NAME,
                key_schema[0]["AttributeName"]
            )
        indexes = {primary_key.name: primary_key}
        if "GlobalSecondaryIndexes" in self._table_meta:
            indexes = {
                **indexes,
                **extract_indexes(self._table_meta["GlobalSecondaryIndexes"], IndexType.GLOBAL_INDEX)
            }
        if "LocalSecondaryIndexes" in self._table_meta:
            indexes = {
                **indexes,
                **extract_indexes(self._table_meta["LocalSecondaryIndexes"], IndexType.LOCAL_INDEX)
            }
        self._indexes = indexes

    def _get_indexes_for_field_list(self, fields: List[str]) -> Dict[str, Index]:
        available_indexes = {}
        for index in self.indexes.values():
            if index.partition_key not in fields:
                continue

            if not index.sort_key:
                available_indexes[index.name] = index
                continue

            if index.sort_key not in fields:
                continue

            available_indexes[index.name] = index

        return available_indexes

    def _validate_table_primary_key(self) -> None:
        if self.partition_key not in self._item_class:
            raise AttributeError(
                f"Table `{self.table_name}` defines partition key {self.partition_key}, "
                f"which was not found in the item class `{self._item_class}`"
            )
        if self.sort_key and self.sort_key not in self._item_class:
            raise AttributeError(
                f"Table `{self.table_name}` defines sort key {self.sort_key}, "
                f"which was not found in the item class `{self._item_class}`"
            )

    @cached_property
    def _prevent_override_condition(self) -> str:
        if self.sort_key:
            return f"attribute_not_exists({self.partition_key}) AND attribute_not_exists({self.sort_key})"

        return f"attribute_not_exists({self.partition_key})"

    def put_item(self, item: I, override: bool = True):
        if not isinstance(item, self._item_class):
            ValueError(f"Could not persist item of type `{type(item)}`, expected instance of `{self._item_class}` instead.")

        try:
            put_query = {
                "TableName": self._table_name,
                "Item": _serialize_item(item.extract())["M"],
                "ReturnConsumedCapacity": "TOTAL",

            }
            if not override:
                put_query["ConditionExpression"] = self._prevent_override_condition

            result = self._db_client.put_item(**put_query)
        except ClientError as e:
            result = e.response

    def get_item(self, *keys: str, consistent_read: bool = False) -> I:
        key_query = {
            self.partition_key: keys[0]
        }
        if len(keys) > 1:
            key_query[self.sort_key] = keys[1]

        key_expression = _serialize_item(key_query)["M"]
        projection = ", ".join(self._item_class.attributes)
        try:
            result = self._db_client.get_item(
                TableName=self.table_name,
                ProjectionExpression=projection,
                Key=key_expression,
                ConsistentRead=consistent_read,
            )
        except ClientError as e:
            raise QueryError(
                f"Retrieving item using query `{key_query}` failed with message: " + e.response["Error"]["Message"],
                key_query,
            ) from e

        if "Item" not in result:
            raise ItemNotFoundError(
                f"Could not retrieve item `{self._item_class}` matching criteria `{key_query}`",
                key_query
            )

        return self._item_class.hydrate(_deserialize_item({"M": result["Item"]}))

    @property
    def indexes(self) -> Dict[str, Index]:
        return self._indexes

    @property
    def table_name(self) -> str:
        return self._table_name

    @cached_property
    def available_indexes(self) -> Dict[str, Index]:
        return self._get_indexes_for_field_list(list(self._item_class.__meta__.keys()))

    @classmethod
    def __class_getitem__(cls, item: Type[Item]) -> Type[Table]:
        return type(f"Table[{item.__module__}.{item.__qualname__}]", tuple([Table]), {"__item_class__": item})  # type: ignore

    @cached_property
    def primary_key(self) -> Index:
        return self.indexes[self._PRIMARY_KEY_NAME]

    @cached_property
    def partition_key(self) -> str:
        return self.primary_key.partition_key

    @cached_property
    def sort_key(self):
        return self.primary_key.sort_key

    @cached_property
    def _item_class(self) -> Union[None, Type[Item]]:
        if hasattr(self, "__item_class__"):
            return getattr(self, "__item_class__")
        return None
