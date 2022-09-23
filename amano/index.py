from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

from .constants import ATTRIBUTE_NAME, KEY_SCHEMA, KEY_TYPE_HASH, KEY_TYPE_RANGE


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
        key_schema = index_data[KEY_SCHEMA]
        if len(key_schema) > 1:
            if key_schema[0]["KeyType"] == KeyType.PARTITION_KEY:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[0][ATTRIBUTE_NAME],
                    key_schema[1][ATTRIBUTE_NAME],
                )
            else:
                index = Index(
                    index_type,
                    index_data["IndexName"],
                    key_schema[1][ATTRIBUTE_NAME],
                    key_schema[0][ATTRIBUTE_NAME],
                )
        else:
            index = Index(
                index_type,
                index_data["IndexName"],
                key_schema[0][ATTRIBUTE_NAME],
            )
        indexes[index.name] = index

    return indexes
