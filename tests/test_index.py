from amano import (
    Attribute,
    GlobalSecondaryIndex,
    Index,
    LocalSecondaryIndex,
    NamedIndex,
    PrimaryKey,
)
from amano.index import Projection


def test_can_instantiate_primary_key() -> None:
    # given
    attribute = Attribute[str]("partition_key")
    index = PrimaryKey(attribute)

    # then
    assert isinstance(index, Index)
    assert str(index) == "#<partition_key>"


def test_can_instantiate_composed_primary_key() -> None:
    # given
    pk = Attribute[str]("partition_key")
    sk = Attribute[str]("sort_key")
    index = PrimaryKey(pk, sk)

    # then
    assert isinstance(index, Index)
    assert str(index) == "#<partition_key;sort_key>"


def test_can_instantiate_local_secondary_index() -> None:
    # given
    attribute = Attribute[str]("partition_key")

    index = LocalSecondaryIndex("IndexName", attribute)

    # then
    assert isinstance(index, Index)
    assert str(index) == "IndexName"


def test_can_instantiate_composed_local_secondary_index() -> None:
    # given
    pk = Attribute[str]("partition_key")
    sk = Attribute[str]("sort_key")

    index = LocalSecondaryIndex("IndexName", pk, sk)

    # then
    assert isinstance(index, Index)
    assert isinstance(index, LocalSecondaryIndex)
    assert str(index) == "IndexName"


def test_can_instantiate_global_secondary_index() -> None:
    # given
    pk = Attribute[str]("partition_key")

    # when
    index = GlobalSecondaryIndex("IndexName", pk)

    # then
    assert isinstance(index, Index)
    assert isinstance(index, NamedIndex)
    assert str(index) == "IndexName"


def test_can_create_composed_global_secondary_index() -> None:
    # given
    pk = Attribute[str]("partition_key")
    sk = Attribute[str]("sort_key")

    # when
    index = GlobalSecondaryIndex("IndexName", pk, sk)

    # then
    assert isinstance(index, Index)
    assert isinstance(index, NamedIndex)
    assert str(index) == "IndexName"


def test_can_cast_index_to_dict() -> None:
    # given
    pk = Attribute[str]("partition_key")
    sk = Attribute[str]("sort_key")
    index = GlobalSecondaryIndex("IndexName", pk, sk)

    # when
    result = index.as_dict()

    # then
    assert result == {
        "IndexName": "IndexName",
        "KeySchema": [
            {"AttributeName": "partition_key", "KeyType": "HASH"},
            {"AttributeName": "sort_key", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    }


def test_can_cast_index_with_all_details_to_dict() -> None:
    # given
    pk = Attribute[str]("partition_key")
    sk = Attribute[str]("sort_key")
    index = GlobalSecondaryIndex("IndexName", pk, sk)
    index.projection = Projection.keys_only()
    index.use_provisioning(10, 5)

    # when
    result = index.as_dict()

    # then
    assert result == {
        "IndexName": "IndexName",
        "KeySchema": [
            {"AttributeName": "partition_key", "KeyType": "HASH"},
            {"AttributeName": "sort_key", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "KEYS_ONLY"},
        "ProvisionedThroughput": {
            "ReadCapacityUnits": 10,
            "WriteCapacityUnits": 5,
        },
    }
