from __future__ import annotations

from typing import Any, Dict, List, Optional

from mypy_boto3_dynamodb import DynamoDBClient

from .attribute import Attribute
from .base_attribute import AttributeType
from .constants import (
    ATTRIBUTE_DEFINITIONS,
    ATTRIBUTE_NAME,
    ATTRIBUTE_TYPE,
    BILLING_MODE,
    GLOBAL_SECONDARY_INDEXES,
    KEY_SCHEMA,
    LOCAL_SECONDARY_INDEXES,
    POINT_IN_TIME_RECOVERY_ENABLED,
    POINT_IN_TIME_RECOVERY_SPECIFICATION,
    PRIMARY_KEY_NAME,
    PROVISIONED_THROUGHPUT,
    TABLE_NAME,
    TTL_SPECIFICATION,
)
from .errors import SchemaError
from .index import (
    GlobalSecondaryIndex,
    Index,
    LocalSecondaryIndex,
    NamedIndex,
    PrimaryKey,
    ProvisionedThroughput,
)
from .utils import StringEnum


class BillingMode(StringEnum):
    PROVISIONED = "PROVISIONED"
    PAY_PER_REQUEST = "PAY_PER_REQUEST"


class TableSchema:
    def __init__(self, table_name: str, key_schema: PrimaryKey):
        self._billing_mode = BillingMode.PAY_PER_REQUEST
        self.table_name = table_name
        self.tags: Dict[str, str] = {}
        self.point_in_time_recovery = False
        self.key_schema = key_schema
        self._indexes: Dict[str, Index] = {PRIMARY_KEY_NAME: key_schema}
        self.provisioned_throughput = ProvisionedThroughput.empty()
        self._ttl_attribute: Optional[Attribute] = None

    def use_provisioning(
        self, read_capacity_units: int, write_capacity_units: int
    ) -> None:
        self._billing_mode = BillingMode.PROVISIONED
        self.provisioned_throughput = ProvisionedThroughput(
            read_capacity_units, write_capacity_units
        )

    def enable_ttl(self, attribute: Attribute) -> None:
        if attribute.type != AttributeType.NUMBER:
            raise SchemaError.for_invalid_ttl_attribute(attribute)

        self._ttl_attribute = attribute

    @property
    def attributes(self) -> List[Attribute]:
        attributes = {
            self.key_schema.partition_key.name: self.key_schema.partition_key
        }
        if self.key_schema.sort_key:
            attributes[self.key_schema.sort_key.name] = self.key_schema.sort_key

        for index in self._indexes.values():
            attributes[index.partition_key.name] = index.partition_key
            if index.sort_key:
                attributes[index.sort_key.name] = index.sort_key

        if self._ttl_attribute:
            attributes[self._ttl_attribute.name] = self._ttl_attribute

        return list(attributes.values())

    def add_index(self, index: NamedIndex) -> None:
        if isinstance(index, LocalSecondaryIndex):
            if index.partition_key.name != self.key_schema.partition_key.name:
                raise SchemaError.for_invalid_partition_key(index)
        self._indexes[index.index_name] = index

    @property
    def indexes(self) -> List[Index]:
        return list(self._indexes.values())

    def as_dict(self) -> Dict[str, Any]:
        result = {
            TABLE_NAME: self.table_name,
            KEY_SCHEMA: self.key_schema.as_dict()[KEY_SCHEMA],
        }
        self._recovery_as_dict(result)
        self._billing_mode_as_dict(result)
        self._indexes_as_dict(result)
        self._attributes_as_dict(result)
        self._ttl_as_dict(result)

        return result

    def _ttl_as_dict(self, result) -> None:
        if not self._ttl_attribute:
            return

        result[TTL_SPECIFICATION] = {
            "Enabled": True,
            ATTRIBUTE_NAME: self._ttl_attribute.name,
        }

    def _attributes_as_dict(self, result):
        result[ATTRIBUTE_DEFINITIONS] = []
        for attribute in self.attributes:
            result[ATTRIBUTE_DEFINITIONS].append(
                {
                    ATTRIBUTE_NAME: attribute.name,
                    ATTRIBUTE_TYPE: str(attribute.type),
                }
            )

    def _recovery_as_dict(self, result):
        if self.point_in_time_recovery:
            result[POINT_IN_TIME_RECOVERY_SPECIFICATION] = {
                POINT_IN_TIME_RECOVERY_ENABLED: self.point_in_time_recovery
            }

    def _billing_mode_as_dict(self, result):
        result[BILLING_MODE] = str(self._billing_mode)
        if self._billing_mode == BillingMode.PROVISIONED:
            if not self.provisioned_throughput:
                raise SchemaError.for_missing_throughput_specification()
            result[
                PROVISIONED_THROUGHPUT
            ] = self.provisioned_throughput.as_dict()  # noqa

    def _indexes_as_dict(self, result: Dict[str, Any]) -> None:
        global_secondary_indexes = []
        local_secondary_indexes = []
        for index in self.indexes:
            if isinstance(index, GlobalSecondaryIndex):
                global_secondary_indexes.append(index.as_dict())
                continue
            if isinstance(index, LocalSecondaryIndex):
                local_secondary_indexes.append(index.as_dict())
        if global_secondary_indexes:
            result[GLOBAL_SECONDARY_INDEXES] = global_secondary_indexes
        if local_secondary_indexes:
            result[LOCAL_SECONDARY_INDEXES] = local_secondary_indexes

    def publish(self, db_client: DynamoDBClient) -> None:
        db_client.create_table(**self.as_dict())
