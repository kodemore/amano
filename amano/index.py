from __future__ import annotations

from typing import Any, Dict, List

from .constants import (
    ATTRIBUTE_NAME,
    GLOBAL_SECONDARY_INDEXES,
    KEY_SCHEMA,
    KEY_TYPE_HASH,
    KEY_TYPE_RANGE,
    LOCAL_SECONDARY_INDEXES,
    PRIMARY_KEY_NAME,
)
from .utils import StringEnum


class KeyType(StringEnum):
    PARTITION_KEY = KEY_TYPE_HASH
    SORT_KEY = KEY_TYPE_RANGE


class IndexType(StringEnum):
    LOCAL_INDEX = "local_index"
    GLOBAL_INDEX = "global_index"
    PRIMARY_KEY = "primary_key"


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

    def __str__(self) -> str:
        return self.name


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
