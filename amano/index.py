from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from .attribute import Attribute
from .constants import (
    ATTRIBUTE_NAME,
    GLOBAL_SECONDARY_INDEXES,
    KEY_SCHEMA,
    KEY_TYPE_HASH,
    KEY_TYPE_RANGE,
    LOCAL_SECONDARY_INDEXES,
    PRIMARY_KEY_NAME, INDEX_NAME, KEY_TYPE, PROJECTION,
    PROJECTION_TYPE_KEYS_ONLY, PROJECTION_TYPE_INCLUDE, PROJECTION_TYPE_ALL,
    PROJECTION_TYPE, NON_KEY_ATTRIBUTES, PROVISIONED_THROUGHPUT,
    WRITE_CAPACITY_UNITS, READ_CAPACITY_UNITS
)
from .utils import StringEnum

StringAttribute = Union[str, Attribute]


class ProjectionType(StringEnum):
    KEYS_ONLY = PROJECTION_TYPE_KEYS_ONLY
    INCLUDE = PROJECTION_TYPE_INCLUDE
    ALL = PROJECTION_TYPE_ALL


@dataclass
class ProvisionedThroughput:
    read_capacity_units: int
    write_capacity_units: int

    @classmethod
    def empty(cls) -> ProvisionedThroughput:
        return cls(0, 0)

    def __bool__(self):
        if self.read_capacity_units == 0 or self.write_capacity_units == 0:
            return False
        return True

    def as_dict(self) -> Dict[str]:
        return {
            WRITE_CAPACITY_UNITS: self.write_capacity_units,
            READ_CAPACITY_UNITS: self.read_capacity_units,
        }


@dataclass
class Projection:
    type: ProjectionType
    non_key_attributes: List[str] = field(default_factory=list)

    @classmethod
    def all(cls) -> Projection:
        return Projection(ProjectionType.ALL)

    @classmethod
    def keys_only(cls) -> Projection:
        return Projection(ProjectionType.KEYS_ONLY)

    @classmethod
    def include(cls, *attribute: Attribute) -> Projection:
        items = []
        for item in attribute:
            items.append(item if isinstance(item, str) else item.name)

        return Projection(ProjectionType.INCLUDE, items)

    def as_dict(self) -> Dict[str, Any]:
        result = {
            PROJECTION_TYPE: str(self.type),
        }

        if self.type == ProjectionType.INCLUDE:
            result[NON_KEY_ATTRIBUTES] = self.non_key_attributes

        return result


class KeyType(StringEnum):
    PARTITION_KEY = KEY_TYPE_HASH
    SORT_KEY = KEY_TYPE_RANGE


class Index(ABC):
    partition_key: Attribute
    sort_key: Attribute

    def __init__(
        self,
        partition_key: Attribute,
        sort_key: Attribute = None
    ):
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.projection = Projection.all()

    def as_dict(self) -> Dict[str, Any]:
        key_schema = [{
            ATTRIBUTE_NAME: self.partition_key.name,
            KEY_TYPE: KEY_TYPE_HASH
        }]

        if self.sort_key:
            key_schema.append({
                ATTRIBUTE_NAME: self.sort_key.name,
                KEY_TYPE: KEY_TYPE_RANGE,
            })

        return {
            KEY_SCHEMA: key_schema,
            PROJECTION: self.projection.as_dict(),
        }


class PrimaryKey(Index):
    pass


class NamedIndex(Index, ABC):
    def __init__(
        self,
        index_name: str,
        partition_key: Attribute,
        sort_key: Attribute = None
    ):
        self.index_name = index_name
        super().__init__(partition_key, sort_key)

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()
        result[INDEX_NAME] = self.index_name

        return result


class GlobalSecondaryIndex(NamedIndex):
    def __init__(
        self,
        index_name: str,
        partition_key: Attribute,
        sort_key: Attribute = None
    ):
        super().__init__(index_name, partition_key, sort_key)
        self.provisioned_throughput = ProvisionedThroughput.empty()

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()
        if self.provisioned_throughput:
            result[PROVISIONED_THROUGHPUT] = self.provisioned_throughput.as_dict()

        return result


class LocalSecondaryIndex(NamedIndex):
    pass


def _extract_index(
    key_schema: List[Dict[str, Any]], index_name: str, index_type: IndexType
) -> Index:
    if len(key_schema) > 1:
        if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
            return Index(
                index_type,
                index_name,
                key_schema[0][ATTRIBUTE_NAME],
                key_schema[1][ATTRIBUTE_NAME],
            )

        return Index(
            index_type,
            index_name,
            key_schema[1][ATTRIBUTE_NAME],
            key_schema[0][ATTRIBUTE_NAME],
        )

    return Index(
        index_type,
        index_name,
        key_schema[0][ATTRIBUTE_NAME],
    )


def _extract_index_list(
    index_list: List[Dict[str, Any]], index_type: IndexType
) -> Dict[str, Index]:
    indexes = {}
    for index_data in index_list:
        if (
            "IndexStatus" in index_data
            and index_data["IndexStatus"] != "ACTIVE"
        ):
            continue

        key_schema = index_data[KEY_SCHEMA]
        index = _extract_index(key_schema, index_data["IndexName"], index_type)
        indexes[index.name] = index

    return indexes


def create_indexes_from_schema(table_schema: Dict[str, List[Dict[str, Any]]]):
    primary_key = _extract_index(
        table_schema[KEY_SCHEMA], PRIMARY_KEY_NAME, IndexType.PRIMARY_KEY
    )
    indexes = {primary_key.name: primary_key}
    if GLOBAL_SECONDARY_INDEXES in table_schema:
        indexes = {
            **indexes,
            **_extract_index_list(
                table_schema[GLOBAL_SECONDARY_INDEXES],
                IndexType.GLOBAL_INDEX,
            ),
        }
    if LOCAL_SECONDARY_INDEXES in table_schema:
        indexes = {
            **indexes,
            **_extract_index_list(
                table_schema[LOCAL_SECONDARY_INDEXES],
                IndexType.LOCAL_INDEX,
            ),
        }
    return indexes
