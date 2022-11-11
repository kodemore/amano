from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .attribute import Attribute
from .constants import (
    ATTRIBUTE_NAME,
    INDEX_NAME,
    KEY_SCHEMA,
    KEY_TYPE,
    KEY_TYPE_HASH,
    KEY_TYPE_RANGE,
    NON_KEY_ATTRIBUTES,
    PROJECTION,
    PROJECTION_TYPE,
    PROJECTION_TYPE_ALL,
    PROJECTION_TYPE_INCLUDE,
    PROJECTION_TYPE_KEYS_ONLY,
    PROVISIONED_THROUGHPUT,
    READ_CAPACITY_UNITS,
    WRITE_CAPACITY_UNITS,
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

    def as_dict(self) -> Dict[str, Any]:
        return {
            READ_CAPACITY_UNITS: self.read_capacity_units,
            WRITE_CAPACITY_UNITS: self.write_capacity_units,
        }

    @classmethod
    def from_dict(cls, value: dict) -> ProvisionedThroughput:
        return cls(value[READ_CAPACITY_UNITS], value[WRITE_CAPACITY_UNITS])


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
    def include(cls, *attribute: Union[str, Attribute]) -> Projection:
        items = []
        for item in attribute:
            items.append(item if isinstance(item, str) else item.name)

        return Projection(ProjectionType.INCLUDE, items)

    def as_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            PROJECTION_TYPE: str(self.type),
        }

        if self.type == ProjectionType.INCLUDE:
            result[NON_KEY_ATTRIBUTES] = self.non_key_attributes

        return result

    @classmethod
    def from_dict(cls, value: dict) -> Projection:
        if value["ProjectionType"] == PROJECTION_TYPE_ALL:
            return Projection.all()

        if value["ProjectionType"] == PROJECTION_TYPE_KEYS_ONLY:
            return Projection.keys_only()

        if value["ProjectionType"] == PROJECTION_TYPE_INCLUDE:
            return Projection.include(*value[NON_KEY_ATTRIBUTES])

        return Projection.all()


class KeyType(StringEnum):
    PARTITION_KEY = KEY_TYPE_HASH
    SORT_KEY = KEY_TYPE_RANGE


class Index(ABC):
    partition_key: Attribute
    sort_key: Optional[Attribute]

    def __init__(self, partition_key: Attribute, sort_key: Attribute = None):
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.projection = Projection.all()

    def as_dict(self) -> Dict[str, Any]:
        key_schema = [
            {ATTRIBUTE_NAME: self.partition_key.name, KEY_TYPE: KEY_TYPE_HASH}
        ]

        if self.sort_key:
            key_schema.append(
                {
                    ATTRIBUTE_NAME: self.sort_key.name,
                    KEY_TYPE: KEY_TYPE_RANGE,
                }
            )

        return {
            KEY_SCHEMA: key_schema,
            PROJECTION: self.projection.as_dict(),
        }


class PrimaryKey(Index):
    NAME = "#"

    def __str__(self) -> str:
        result = f"{self.NAME}<{self.partition_key}"
        if self.sort_key:
            result += f";{self.sort_key}"

        return result + ">"


class NamedIndex(Index, ABC):
    def __init__(
        self,
        index_name: str,
        partition_key: Attribute,
        sort_key: Attribute = None,
    ):
        self.index_name = index_name
        super().__init__(partition_key, sort_key)

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()
        result[INDEX_NAME] = self.index_name

        return result

    def __str__(self) -> str:
        return self.index_name


class GlobalSecondaryIndex(NamedIndex):
    def __init__(
        self,
        index_name: str,
        partition_key: Attribute,
        sort_key: Attribute = None,
    ):
        super().__init__(index_name, partition_key, sort_key)
        self.provisioned_throughput = ProvisionedThroughput.empty()

    def use_provisioning(
        self, read_capacity_units: int, write_capacity_units: int
    ) -> None:
        self.provisioned_throughput = ProvisionedThroughput(
            read_capacity_units, write_capacity_units
        )

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()
        if self.provisioned_throughput:
            result[
                PROVISIONED_THROUGHPUT
            ] = self.provisioned_throughput.as_dict()

        return result


class LocalSecondaryIndex(NamedIndex):
    pass
