from __future__ import annotations

from abc import ABC
from enum import Enum
from functools import cached_property
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
    Set,
    Iterator,
    Generator,
    Iterable, Callable,
)

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError, ParamValidationError
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.service_resource import Table as DynamoDBTable
from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef

from .attribute import Attribute
from .base_attribute import AttributeValue
from .condition import Condition
from .constants import (
    KEY_TYPE_HASH,
    KEY_TYPE_RANGE,
    CONDITION_LOGICAL_OR,
    SELECT_SPECIFIC_ATTRIBUTES,
    CONDITION_FUNCTION_CONTAINS,
)
from .errors import ItemNotFoundError, QueryError
from .item import Item, _AttributeChange, _ChangeType

I = TypeVar("I", bound=Item)

_serialize_item = TypeSerializer().serialize
_deserialize_item = TypeDeserializer().deserialize

KeyExpression = Dict[str, AttributeValueTypeDef]


class KeyType(Enum):
    PARTITION_KEY = KEY_TYPE_HASH
    SORT_KEY = KEY_TYPE_RANGE

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other

        return other == self


class IndexType(Enum):
    LOCAL_INDEX = "local_index"
    GLOBAL_INDEX = "global_index"
    PRIMARY_KEY = "primary_key"


class Cursor(Generic[I]):
    def __init__(
        self, item_class: Type[I], query: Dict[str, Any], executor: Callable
    ):
        self._executor = executor
        self.query = query
        self.hydrate = True
        self._item_class = item_class
        self._fetched_records: List[Dict[str, AttributeValue]] = []
        self._current_index = 0
        self._exhausted = False
        self._last_evaluated_key: Dict[str, AttributeValue] = {}

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
            result = self._executor(**self.query)
        except Exception as e:
            self._fetched_records = []
            self._exhausted = True
            raise QueryError(
                f"Could not execute query "
                f"`{self.query['KeyConditionExpression']}`, reason: {e}"
            )
        if "LastEvaluatedKey" in result:
            self._last_evaluated_key = result["LastEvaluatedKey"]
            self.query["ExclusiveStartKey"] = result["LastEvaluatedKey"]
        else:
            self._exhausted = True

        self._fetched_records = self._fetched_records + result["Items"]


class Index:
    def __init__(
        self,
        index_type: IndexType,
        name: str,
        partition_key: str,
        sort_key: str = "",
    ):
        self.index_type = index_type
        self.name = name
        self.partition_key = partition_key
        self.sort_key = sort_key


def extract_indexes(
    index_list: List[Dict[str, Any]], index_type: IndexType
) -> Dict[str, Index]:
    indexes = {}
    for index_data in index_list:
        if (
            "IndexStatus" in index_data
            and index_data["IndexStatus"] != "ACTIVE"
        ):
            continue
        key_schema = index_data["KeySchema"]
        if len(key_schema) > 1:
            if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[0]["AttributeName"],
                    key_schema[1]["AttributeName"],
                )
            else:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[1]["AttributeName"],
                    key_schema[0]["AttributeName"],
                )
        else:
            index = Index(
                index_type,
                index_data["IndexName"],
                key_schema[0]["AttributeName"],
            )
        indexes[index.name] = index

    return indexes


class Table(Generic[I]):
    _PRIMARY_KEY_NAME = "#"
    __item_class__: Type[Item]

    def __init__(self, db_client: DynamoDBClient, table_name: str):
        if not self._item_class:
            raise SyntaxError(
                f"{self.__class__} must be parametrized with a "
                f"subtype of {Item.__module__}.{Item.__qualname__}"
            )

        self._db_client = db_client
        self._table_name = table_name
        self._table_meta: Dict[str, Any] = {}
        self._fetch_table_meta(table_name)
        self._hydrate_indexes()
        self._validate_table_primary_key()

    def _fetch_table_meta(self, table_name):
        try:
            self._table_meta = self._db_client.describe_table(
                TableName=self._table_name
            )["Table"]
        except ClientError as e:
            raise ValueError(
                f"Table with name {table_name} was not found"
            ) from e
        except KeyError as e:
            raise ValueError(
                f"There was an error while retrieving "
                f"`{table_name}` information."
            ) from e

    def _hydrate_indexes(self):
        key_schema = self._table_meta.get("KeySchema")
        if len(key_schema) > 1:
            if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
                primary_key = Index(
                    IndexType.PRIMARY_KEY,
                    self._PRIMARY_KEY_NAME,
                    key_schema[0]["AttributeName"],
                    key_schema[1]["AttributeName"],
                )
            else:
                primary_key = Index(
                    IndexType.PRIMARY_KEY,
                    self._PRIMARY_KEY_NAME,
                    key_schema[1]["AttributeName"],
                    key_schema[0]["AttributeName"],
                )
        else:
            primary_key = Index(
                IndexType.PRIMARY_KEY,
                self._PRIMARY_KEY_NAME,
                key_schema[0]["AttributeName"],
            )
        indexes = {primary_key.name: primary_key}
        if "GlobalSecondaryIndexes" in self._table_meta:
            indexes = {
                **indexes,
                **extract_indexes(
                    self._table_meta["GlobalSecondaryIndexes"],
                    IndexType.GLOBAL_INDEX,
                ),
            }
        if "LocalSecondaryIndexes" in self._table_meta:
            indexes = {
                **indexes,
                **extract_indexes(
                    self._table_meta["LocalSecondaryIndexes"],
                    IndexType.LOCAL_INDEX,
                ),
            }
        self._indexes = indexes

    def _get_indexes_for_field_list(
        self, fields: List[str]
    ) -> Dict[str, Index]:
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
                f"Table `{self.table_name}` defines partition key "
                f"{self.partition_key}, which was not found in the item class "
                f"`{self._item_class}`"
            )
        if self.sort_key and self.sort_key not in self._item_class:
            raise AttributeError(
                f"Table `{self.table_name}` defines sort key {self.sort_key}, "
                f"which was not found in the item class `{self._item_class}`"
            )

    @cached_property
    def _prevent_override_condition(self) -> str:
        if self.sort_key:
            return f"attribute_not_exists({self.partition_key}) AND " \
                   f"attribute_not_exists({self.sort_key})"

        return f"attribute_not_exists({self.partition_key})"

    def save(self, item: I) -> None:
        ...

    def put(self, item: I, condition: Condition = None) -> bool:
        if not isinstance(item, self._item_class):
            ValueError(
                f"Could not persist item of type `{type(item)}`, "
                f"expected instance of `{self._item_class}` instead."
            )
        try:
            put_query = {
                "TableName": self._table_name,
                "Item": item.extract(),
                "ReturnConsumedCapacity": "TOTAL",
            }
            if condition:
                put_query["ConditionExpression"] = str(condition)
                if condition.values:
                    put_query["ExpressionAttributeValues"] = condition.values

            result = self._db_client.put_item(**put_query)  # type: ignore
        except ClientError as e:
            error = e.response.get("Error")
            if error["Code"] == "ConditionalCheckFailedException":
                return False
            raise QueryError(error["Message"]) from e
        except ParamValidationError as e:
            raise QueryError(str(e)) from e

        return result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def update(self, item: I) -> None:
        (
            update_expression,
            expression_attribute_values,
        ) = self._generate_update_expression(item)

        self._db_client.update_item(
            TableName=self._table_name,
            Key=self._get_key_expression(item),
            UpdateExpression=...,
            ExpressionAttributeValues=...,
        )
        ...

    def _generate_update_expression(
        self, item: I
    ) -> Tuple[str, Dict[str, Any]]:

        changes = {
            attribute_change.attribute.name: attribute_change
            for attribute_change in item.__log__
        }

        set_fields = []
        delete_fields = []
        attribute_values = {}
        for change in changes.values():
            if change.type in (_ChangeType.CHANGE, _ChangeType.SET):
                set_fields.append(change.attribute.name)
                attribute_values[":" + change.attribute.name] = _serialize_item(
                    change.attribute.extract(change.value)
                )
                continue
            if change.type is _ChangeType.UNSET:
                delete_fields.append(change.attribute.name)

        update_expression = ""
        if set_fields:
            set_fields_expression = ','.join(
                [field_name + ' = :' + field_name for field_name in set_fields]
            )
            update_expression = f"SET {set_fields_expression} "
        if delete_fields:
            update_expression += (
                f"DELETE {','.join([field_name for field_name in set_fields])} "
            )

        return update_expression, attribute_values

    def query(
        self,
        key_condition: Condition,
        filter_condition: Condition = None,
        limit: int = 0,
        use_index: Union[Index, str] = None,
    ) -> Cursor:
        key_condition_expression = str(key_condition)
        key_attributes = list(key_condition.attributes)
        if len(key_attributes) > 2:
            raise QueryError(
                f"Could not execute query `{key_condition_expression}`, "
                f"too many attributes in key_condition."
            )

        if any(
            operator in key_condition_expression
            for operator in [CONDITION_LOGICAL_OR, CONDITION_FUNCTION_CONTAINS]
        ):
            raise QueryError(
                f"Could not execute query `{key_condition_expression}`, "
                "used operator is not supported."
            )
        key_condition_values = key_condition.values
        projection = ", ".join(self.attributes)

        if use_index:
            if isinstance(use_index, str):
                if use_index not in self.indexes:
                    raise QueryError(
                        f"Used unknown index `{use_index}` in query "
                        f"`{key_condition_expression}` "
                    )
                hint_index = self.indexes[use_index]
            else:
                hint_index = use_index
        else:
            hint_index = self._hint_index_for_attributes(key_attributes)

        query = {
            "TableName": self._table_name,
            "Select": SELECT_SPECIFIC_ATTRIBUTES,
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeValues": key_condition_values,
            "ProjectionExpression": projection,
            "ReturnConsumedCapacity": "INDEXES",
        }

        if hint_index.name != self._PRIMARY_KEY_NAME:
            query["IndexName"] = hint_index.name

        if filter_condition:
            query["FilterExpression"] = str(filter_condition)
            query["ExpressionAttributeValues"] = {
                **query["ExpressionAttributeValues"],
                **filter_condition.values,
            }

        if limit:
            query["Limit"] = limit

        return Cursor(self._item_class, query, self._db_client.query)

    def get(self, *keys: str, consistent_read: bool = False) -> I:
        key_query = {self.partition_key: keys[0]}
        if len(keys) > 1:
            key_query[self.sort_key] = keys[1]

        key_expression = _serialize_item(key_query)["M"]
        projection = ", ".join(self.attributes)
        try:
            result = self._db_client.get_item(
                TableName=self.table_name,
                ProjectionExpression=projection,
                Key=key_expression,
                ConsistentRead=consistent_read,
            )
        except ClientError as e:
            raise QueryError(
                f"Retrieving item using query `{key_query}` "
                f"failed with message: {e.response['Error']['Message']}",
                key_query,
            ) from e

        if "Item" not in result:
            raise ItemNotFoundError(
                f"Could not retrieve item `{self._item_class}` "
                f"matching criteria `{key_query}`",
                key_query,
            )

        return self._item_class.hydrate(result["Item"])

    def _get_key_expression(self, item: I) -> KeyExpression:
        key_expression = {
            self.partition_key: getattr(item, self.partition_key),
        }

        if self.sort_key:
            key_expression[self.sort_key] = getattr(item, self.sort_key)

        return _serialize_item(key_expression)

    @property
    def indexes(self) -> Dict[str, Index]:
        return self._indexes

    @property
    def table_name(self) -> str:
        return self._table_name

    @cached_property
    def available_indexes(self) -> Dict[str, Index]:
        return self._get_indexes_for_field_list(
            list(self._item_class.__meta__.keys())
        )

    @classmethod
    def __class_getitem__(cls, item: Type[Item]) -> Type[Table]:
        return type(  # type: ignore
            f"Table[{item.__module__}.{item.__qualname__}]",
            tuple([Table]),
            {"__item_class__": item}
        )

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
    def _item_class(self) -> Type[Item]:
        if hasattr(self, "__item_class__"):
            return getattr(self, "__item_class__")
        raise RuntimeError

    @cached_property
    def attributes(self) -> List[str]:
        return [
            attribute.name for attribute in self._item_class.attributes.values()
        ]

    def _hint_index_for_attributes(self, attributes: List[str]) -> Index:
        if len(attributes) == 1:
            for index in self.indexes.values():
                if index.partition_key == attributes[0]:
                    return index
            raise QueryError(
                f"No GSI index defined for `{attributes[0]}` attribute."
            )

        matched_indexes = []

        for index in self.indexes.values():
            if (
                index.partition_key not in attributes
                or index.sort_key not in attributes
            ):
                continue

            # partition key was on a first place in condition,
            # so we assume the best index here
            if attributes[0] == index.partition_key:
                return index

            matched_indexes.append(index)

        if not matched_indexes:
            raise QueryError(
                f"No GSI/LSI index defined for "
                f"`{'`,`'.join(attributes)}` attributes."
            )

        # return first matched index
        return matched_indexes[0]
