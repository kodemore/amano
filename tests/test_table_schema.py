import pytest

from amano import Attribute, TableSchema
from amano.errors import SchemaError
from amano.index import GlobalSecondaryIndex, LocalSecondaryIndex, PrimaryKey


def test_can_instantiate() -> None:
    # given
    artist_name = Attribute[str]("artist_name")

    # when
    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # then
    assert isinstance(schema, TableSchema)
    assert artist_name in schema.attributes


def test_can_add_global_secondary_index() -> None:
    # given
    album_name = Attribute[str]("album_name")
    artist_name = Attribute[str]("artist_name")
    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # when
    schema.add_index(GlobalSecondaryIndex("GSI1", album_name, artist_name))

    # then
    assert len(schema.indexes) == 2
    assert schema.as_dict() == {
        "TableName": "table_name",
        "KeySchema": [{"AttributeName": "artist_name", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "artist_name", "AttributeType": "S"},
            {"AttributeName": "album_name", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "album_name", "KeyType": "HASH"},
                    {"AttributeName": "artist_name", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    }


def test_can_add_local_secondary_index() -> None:
    # given
    album_name = Attribute[str]("album_name")
    artist_name = Attribute[str]("artist_name")
    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # when
    schema.add_index(LocalSecondaryIndex("LSI1", artist_name, album_name))

    # then
    assert len(schema.indexes) == 2
    assert schema.as_dict() == {
        "TableName": "table_name",
        "KeySchema": [{"AttributeName": "artist_name", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "artist_name", "AttributeType": "S"},
            {"AttributeName": "album_name", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "LocalSecondaryIndexes": [
            {
                "IndexName": "LSI1",
                "KeySchema": [
                    {"AttributeName": "artist_name", "KeyType": "HASH"},
                    {"AttributeName": "album_name", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    }


def test_fail_to_add_local_secondary_index() -> None:
    # given
    album_name = Attribute[str]("album_name")
    artist_name = Attribute[str]("artist_name")
    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # when
    with pytest.raises(SchemaError):
        schema.add_index(LocalSecondaryIndex("LSI1", album_name, album_name))


def test_can_use_provisioned_billing_mode() -> None:
    # given
    album_name = Attribute[str]("album_name")
    artist_name = Attribute[str]("artist_name")
    schema = TableSchema("table_name", PrimaryKey(artist_name, album_name))

    # when
    schema.use_provisioning(1, 2)

    # then
    assert schema.provisioned_throughput.read_capacity_units == 1
    assert schema.provisioned_throughput.write_capacity_units == 2

    assert schema.as_dict() == {
        "TableName": "table_name",
        "KeySchema": [
            {"AttributeName": "artist_name", "KeyType": "HASH"},
            {"AttributeName": "album_name", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "artist_name", "AttributeType": "S"},
            {"AttributeName": "album_name", "AttributeType": "S"},
        ],
        "BillingMode": "PROVISIONED",
        "ProvisionedThroughput": {
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 2,
        },
    }


def test_can_enable_ttl() -> None:
    # given
    artist_name = Attribute[str]("artist_name")
    ttl = Attribute[int]("ttl")

    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # when
    schema.enable_ttl(ttl)

    # then
    assert schema.as_dict() == {
        "TableName": "table_name",
        "KeySchema": [{"AttributeName": "artist_name", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "artist_name", "AttributeType": "S"},
            {"AttributeName": "ttl", "AttributeType": "N"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "TimeToLiveSpecification": {
            "Enabled": True,
            "AttributeName": "ttl",
        },
    }


def test_fail_enabling_ttl() -> None:
    # given
    artist_name = Attribute[str]("artist_name")
    ttl = Attribute[str]("ttl")

    schema = TableSchema("table_name", PrimaryKey(artist_name))

    # when
    with pytest.raises(ValueError):
        schema.enable_ttl(ttl)


def test_can_publish(default_dynamodb_client) -> None:
    try:
        default_dynamodb_client.delete_table(TableName="table_name")
    except Exception:
        pass

    # given
    artist_name = Attribute[str]("artist_name")
    album_name = Attribute[str]("album_name")

    schema = TableSchema("table_name", PrimaryKey(artist_name))
    schema.add_index(GlobalSecondaryIndex("GSI1", album_name, artist_name))

    # when
    schema.publish(default_dynamodb_client)
