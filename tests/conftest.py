from typing import Generator, List, Dict

import pytest
import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient
from botocore.exceptions import ClientError
import json


@pytest.fixture()
def tracks_with_artists_json() -> List[Dict]:
    with open("fixtures/tracks_with_artist.json", "r") as file:
        data = json.load(file)

    return data


@pytest.fixture
def dynamodb_client() -> DynamoDBClient:
    session = boto3.Session(
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="localhost"
    )
    client = session.client("dynamodb", endpoint_url="http://localhost:8000")

    return client


@pytest.fixture
def dynamodb_test_table_name() -> str:
    return "tracks"


@pytest.fixture
def bootstrapped_dynamodb_client(dynamodb_client, dynamodb_test_table_name, tracks_with_artists_json) -> Generator[DynamoDBClient, None, None]:
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
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GlobalAlbumAndTrackNameIndex",
                    "KeySchema": [
                        {"AttributeName": "album_name", "KeyType": "HASH"},
                        {"AttributeName": "track_name", "KeyType": "RANGE"},
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                },
                {
                    "IndexName": "GlobalGenreAndAlbumNameIndex",
                    "KeySchema": [
                        {"AttributeName": "genre_name", "KeyType": "HASH"},
                        {"AttributeName": "album_name", "KeyType": "RANGE"},
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                }
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

    #dynamodb_client.delete_table(
    #    TableName=dynamodb_test_table_name,
    #)

