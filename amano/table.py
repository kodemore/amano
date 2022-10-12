from __future__ import annotations

import typing
from functools import cached_property
from typing import Any, Dict, Generic, List, Type, Union

from botocore.exceptions import ClientError, ParamValidationError
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef

from .base_attribute import serialize_value
from .condition import Condition
from .constants import (
    CONDITION_FUNCTION_CONTAINS,
    CONDITION_LOGICAL_OR,
    SELECT_SPECIFIC_ATTRIBUTES,
)
from .cursor import Cursor
from .errors import (
    DeleteItemError,
    ItemNotFoundError,
    PutItemError,
    QueryError,
    ReadError,
    UpdateItemError,
)
from .index import Index, create_indexes_from_schema
from .item import (
    Item,
    ItemState,
    commit,
    diff,
    extract,
    get_item_state,
    hydrate,
)

KeyExpression = Dict[str, AttributeValueTypeDef]

I = typing.TypeVar("I", bound=Item)


class Table(Generic[I]):
    _PRIMARY_KEY_NAME = "#"
    __item_class__: Type[I]

    def __init__(self, db_client: DynamoDBClient, table_name: str):
        if not hasattr(self, "__item_class__"):
            raise TypeError(
                f"{self.__class__} must be parametrized with a "
                f"subtype of {Item.__module__}.{Item.__qualname__}"
            )

        self._db_client = db_client
        self._table_name = table_name
        self._table_meta: Dict[str, Any] = {}
        self._fetch_table_meta(table_name)
        self._indexes = create_indexes_from_schema(self._table_meta)
        self._validate_table_primary_key()

    def _fetch_table_meta(self, table_name):
        try:
            self._table_meta = self._db_client.describe_table(
                TableName=self._table_name
            )["Table"]
        except ClientError as error:
            raise ValueError(
                f"Table with name {table_name} was not found"
            ) from error
        except KeyError as error:
            raise ValueError(
                f"There was an error while retrieving "
                f"`{table_name}` information."
            ) from error

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
        if self.partition_key not in self._item_class.__schema__:
            raise AttributeError(
                f"Table `{self.table_name}` defines partition key "
                f"{self.partition_key}, which was not found in the item class "
                f"`{self._item_class}`"
            )
        if self.sort_key and self.sort_key not in self._item_class.__schema__:
            raise AttributeError(
                f"Table `{self.table_name}` defines sort key {self.sort_key}, "
                f"which was not found in the item class `{self._item_class}`"
            )

    def scan(
        self,
        condition: Condition = None,
        limit: int = 0,
        use_index: Union[Index, str] = None,
        consistent_read: bool = False,
    ) -> Cursor:
        scan_params = {
            "TableName": self._table_name,
            "ReturnConsumedCapacity": "INDEXES",
            "ConsistentRead": consistent_read,
        }

        if condition:
            scan_params["FilterExpression"] = str(condition)
            if condition.parameters:
                scan_params["ExpressionAttributeValues"] = serialize_value(
                    condition.parameters
                ).get("M")

        if use_index:
            if isinstance(use_index, str):
                if use_index not in self.indexes:
                    raise QueryError.for_invalid_index(use_index, condition)
                hint_index = self.indexes[use_index]
            else:
                hint_index = use_index

            scan_params["IndexName"] = str(hint_index)

        if limit:
            scan_params["Limit"] = limit

        return Cursor(self._item_class, scan_params, self._db_client.scan)

    def save(self, item: I, condition: Condition = None) -> bool:
        item_state = get_item_state(item)
        if item_state == ItemState.NEW:
            return self.put(item, condition)

        if item_state == ItemState.DIRTY:
            return self.update(item, condition)

        return False

    def delete(self, item: I, condition: Condition = None) -> bool:
        if not isinstance(item, self._item_class):
            ValueError(
                f"Could not delete and item of type `{type(item)}`, "
                f"expected instance of `{self._item_class}` instead."
            )
        try:
            query = {
                "TableName": self._table_name,
                "Key": self._get_key_expression(item),
            }

            if condition:
                query["ConditionExpression"] = str(condition)
                query["ExpressionAttributeValues"] = serialize_value(
                    condition.parameters
                ).get("M")

            result = self._db_client.delete_item(**query)  # type: ignore
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "ConditionalCheckFailedException":
                return False
            raise DeleteItemError.for_client_error(error["Message"]) from e
        except ParamValidationError as e:
            raise DeleteItemError.for_validation_error(item, str(e)) from e

        success = result["ResponseMetadata"]["HTTPStatusCode"] == 200

        if success:
            commit(item)

        return success

    def put(self, item: I, condition: Condition = None) -> bool:
        """
        Creates or overrides item in a table for the same PK.

        :param item: an item to be stored
        :param condition: an optional condition on which to put
        :return: `True` on success or `False` on condition failure
        :raises ValueError: when invalid value is passed as an item
        :raises amano.errors.PuItemError: when validation or client fails
        """
        if not isinstance(item, self._item_class):
            ValueError(
                f"Could not persist item of type `{type(item)}`, "
                f"expected instance of `{self._item_class}` instead."
            )
        try:
            put_query = {
                "TableName": self._table_name,
                "Item": extract(item),
                "ReturnConsumedCapacity": "TOTAL",
            }
            if condition:
                put_query["ConditionExpression"] = str(condition)
                if condition.parameters:
                    put_query["ExpressionAttributeValues"] = serialize_value(
                        condition.parameters
                    ).get("M")

            result = self._db_client.put_item(**put_query)  # type: ignore
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "ConditionalCheckFailedException":
                return False
            raise PutItemError.for_client_error(error["Message"]) from e
        except ParamValidationError as e:
            raise PutItemError.for_validation_error(item, str(e)) from e

        success = result["ResponseMetadata"]["HTTPStatusCode"] == 200

        if success:
            commit(item)

        return success

    def update(self, item: I, condition: Condition = None) -> bool:
        if not isinstance(item, self._item_class):
            ValueError(
                f"Could not update item of type `{type(item)}`, "
                f"expected instance of `{self._item_class}` instead."
            )
        item_state = get_item_state(item)
        if item_state == ItemState.CLEAN:
            return False

        if item_state == ItemState.NEW:
            raise UpdateItemError.for_new_item(item)

        (
            update_expression,
            expression_attribute_values,
        ) = diff(item)

        query: Dict[str, Any] = {
            "TableName": self._table_name,
            "Key": self._get_key_expression(item),
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": serialize_value(
                expression_attribute_values
            ).get("M"),
            "ReturnConsumedCapacity": "INDEXES",
        }

        if condition:
            query["ConditionExpression"] = str(condition)
            if condition.parameters:
                query["ExpressionAttributeValues"] = {
                    **query["ExpressionAttributeValues"],
                    **serialize_value(condition.parameters).get("M"),
                }
        try:
            result = self._db_client.update_item(**query)  # type: ignore[arg-type]
        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") == "ConditionalCheckFailedException":
                return False
            raise UpdateItemError.for_client_error(error["Message"]) from e

        success = result["ResponseMetadata"]["HTTPStatusCode"] == 200

        if success:
            commit(item)

        return success

    def query(
        self,
        key_condition: Condition,
        filter_condition: Condition = None,
        limit: int = 0,
        use_index: Union[Index, str] = None,
        consistent_read: bool = False,
    ) -> Cursor[I]:
        key_condition_expression = str(key_condition)
        key_attributes = list(key_condition.hint)
        if len(key_attributes) > 2:
            raise QueryError.for_invalid_key_condition(
                key_condition, "Too many attributes in key_condition."
            )

        if any(
            operator in key_condition_expression
            for operator in [CONDITION_LOGICAL_OR, CONDITION_FUNCTION_CONTAINS]
        ):
            raise QueryError.for_invalid_key_condition(
                key_condition, "Detected unsupported operator."
            )
        key_condition_values = serialize_value(key_condition.parameters).get(
            "M"
        )
        projection = ", ".join(self.attributes)

        if use_index:
            if isinstance(use_index, str):
                if use_index not in self.indexes:
                    raise QueryError.for_invalid_index(use_index, key_condition)
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
            "ConsistentRead": consistent_read,
        }

        if hint_index.name != self._PRIMARY_KEY_NAME:
            query["IndexName"] = hint_index.name

        if filter_condition:
            query["FilterExpression"] = str(filter_condition)
            query["ExpressionAttributeValues"] = {
                **query["ExpressionAttributeValues"],  # type: ignore
                **serialize_value(filter_condition.parameters).get("M"),  # type: ignore
            }

        if limit:
            query["Limit"] = limit

        return Cursor(self._item_class, query, self._db_client.query)

    def get(self, *keys: str, consistent_read: bool = False) -> I:
        key_query = {self.partition_key: keys[0]}
        if len(keys) > 1:
            key_query[self.sort_key] = keys[1]

        key_expression = serialize_value(key_query)["M"]
        projection = ", ".join(self.attributes)
        try:
            result = self._db_client.get_item(
                TableName=self.table_name,
                ProjectionExpression=projection,
                Key=key_expression,
                ConsistentRead=consistent_read,
            )
        except ClientError as e:
            raise ReadError.for_client_error(
                e.response['Error']['Message']
            ) from e

        if "Item" not in result:
            raise ItemNotFoundError(
                f"Could not retrieve item `{self._item_class}` "
                f"matching criteria `{key_query}`",
                key_query,
            )

        return hydrate(self._item_class, result["Item"])

    def _get_key_expression(self, item: I) -> KeyExpression:
        key_expression = {
            self.partition_key: getattr(item, self.partition_key),
        }

        if self.sort_key:
            key_expression[self.sort_key] = getattr(item, self.sort_key)

        return serialize_value(key_expression).get("M")  # type: ignore[return-value]

    @property
    def indexes(self) -> Dict[str, Index]:
        return self._indexes

    @property
    def table_name(self) -> str:
        return self._table_name

    @cached_property
    def available_indexes(self) -> Dict[str, Index]:
        return self._get_indexes_for_field_list(
            list(self._item_class.__schema__.keys())
        )

    @classmethod
    def __class_getitem__(
        cls, item: Type[Item], schema: Any = None
    ) -> Type[Table]:  # noqa: E501
        if not issubclass(item, Item):
            raise TypeError(
                f"Expected subclass of `{Item}`, " f"got {item} instead."
            )
        return type(  # type: ignore
            f"{Table.__qualname__}[{item.__module__}.{item.__qualname__}]",
            tuple([Table]),
            {"__item_class__": item},
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
    def _item_class(self) -> Type[I]:
        if hasattr(self, "__item_class__"):
            return getattr(self, "__item_class__")

        raise AttributeError()

    @cached_property
    def attributes(self) -> List[str]:
        return [
            attribute.name for attribute in self._item_class.__schema__.values()  # type: ignore
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
