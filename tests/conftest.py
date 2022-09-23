import json
import os
from os import path
from typing import Dict, Generator, List

import boto3
import pytest
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.client import DynamoDBClient


@pytest.fixture()
def generic_field_identifier(monkeypatch) -> None:
    monkeypatch.setattr("amano.condition._param_suffix", lambda: "")


@pytest.fixture
def fixtures_dir() -> str:
    return path.join(path.dirname(path.realpath(__file__)), "fixtures")


@pytest.fixture
def tracks_with_artists_json(fixtures_dir) -> List[Dict]:
    with open(path.join(fixtures_dir, "tracks_with_artist.json"), "r") as file:
        data = json.load(file)

    return data


@pytest.fixture
def dynamodb_client() -> DynamoDBClient:
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.environ.get("AWS_REGION_NAME", "localhost"),
    )
    client = session.client(
        "dynamodb",
        endpoint_url=os.environ.get("ENDPOINT_URL", "http://localhost:8000"),
    )

    return client


@pytest.fixture
def readonly_table() -> str:
    return "tracks"


@pytest.fixture
def default_table() -> str:
    return "default_table"


@pytest.fixture
def readonly_dynamodb_client(
    dynamodb_client, readonly_table, tracks_with_artists_json
) -> Generator[DynamoDBClient, None, None]:

    table_info = False
    try:
        table_info = dynamodb_client.describe_table(
            TableName=readonly_table
        )
    except ClientError:
        dynamodb_client.create_table(
            TableName=readonly_table,
            KeySchema=[
                {"AttributeName": "artist_name", "KeyType": "HASH"},
                {"AttributeName": "track_name", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "artist_name", "AttributeType": "S"},
                {"AttributeName": "track_name", "AttributeType": "S"},
                {"AttributeName": "album_name", "AttributeType": "S"},
                {"AttributeName": "genre_name", "AttributeType": "S"},
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "LocalArtistAndAlbumNameIndex",
                    "KeySchema": [
                        {"AttributeName": "artist_name", "KeyType": "HASH"},
                        {"AttributeName": "album_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GlobalAlbumAndTrackNameIndex",
                    "KeySchema": [
                        {"AttributeName": "album_name", "KeyType": "HASH"},
                        {"AttributeName": "track_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
                {
                    "IndexName": "GlobalGenreAndAlbumNameIndex",
                    "KeySchema": [
                        {"AttributeName": "genre_name", "KeyType": "HASH"},
                        {"AttributeName": "album_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    if table_info:
        yield dynamodb_client

        return

    for item in tracks_with_artists_json:
        dynamodb_client.put_item(
            TableName=readonly_table,
            Item={
                "album_name": {"S": item["album_name"]},
                "track_name": {"S": item["track_name"]},
                "genre_name": {"S": item["genre_name"]},
                "media_type_name": {"S": item["media_type_name"]},
                "track_duration": {"N": str(item["track_duration"])},
                "artist_name": {"S": item["artist_name"]},
            },
        )

    yield dynamodb_client


@pytest.fixture
def default_dynamodb_client(
    dynamodb_client, default_table
) -> Generator[DynamoDBClient, None, None]:
    table_info = None
    try:
        table_info = dynamodb_client.describe_table(
            TableName=default_table
        )
    except ClientError:
        dynamodb_client.create_table(
            TableName=default_table,
            KeySchema=[
                {"AttributeName": "artist_name", "KeyType": "HASH"},
                {"AttributeName": "track_name", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "artist_name", "AttributeType": "S"},
                {"AttributeName": "track_name", "AttributeType": "S"},
                {"AttributeName": "album_name", "AttributeType": "S"},
                {"AttributeName": "genre_name", "AttributeType": "S"},
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "LocalArtistAndAlbumNameIndex",
                    "KeySchema": [
                        {"AttributeName": "artist_name", "KeyType": "HASH"},
                        {"AttributeName": "album_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GlobalAlbumAndTrackNameIndex",
                    "KeySchema": [
                        {"AttributeName": "album_name", "KeyType": "HASH"},
                        {"AttributeName": "track_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
                {
                    "IndexName": "GlobalGenreAndAlbumNameIndex",
                    "KeySchema": [
                        {"AttributeName": "genre_name", "KeyType": "HASH"},
                        {"AttributeName": "album_name", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    if table_info:
        yield dynamodb_client

        dynamodb_client.delete_table(TableName=default_table)
        return

    yield dynamodb_client
    dynamodb_client.delete_table(TableName=default_table)
