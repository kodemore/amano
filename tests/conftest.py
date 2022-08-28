import json
import os
from os import path
from typing import Dict, Generator, List

import boto3
import pytest
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.client import DynamoDBClient


@pytest.fixture
def field_identifier() -> str:
    return "_[a-zA-Z]{4}[0-9]"


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
def dynamodb_test_table_name() -> str:
    return "tracks"


@pytest.fixture
def bootstrapped_dynamodb_client(
    dynamodb_client, dynamodb_test_table_name, tracks_with_artists_json
) -> Generator[DynamoDBClient, None, None]:
    try:
        table_exists = False
        dynamodb_client.create_table(
            TableName=dynamodb_test_table_name,
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
    except ClientError as e:
        if e.operation_name == "CreateTable":
            table_exists = True
            yield dynamodb_client  # Table is already created probably due to test failure
        else:
            raise e

    if table_exists:
        return

    for item in tracks_with_artists_json:
        result = dynamodb_client.put_item(
            TableName=dynamodb_test_table_name,
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

    # dynamodb_client.delete_table(
    #    TableName=dynamodb_test_table_name,
    # )
