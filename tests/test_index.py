from amano import Index, Attribute


def test_can_instantiate() -> None:
    # given
    index = Index(Index.LOCAL_INDEX, "IndexName", "partition_key")

    # then
    assert isinstance(index, Index)
    assert str(index) == "LSI@IndexName(partition_key)"


def test_can_instantiate_with_attribute() -> None:
    # given
    attribute = Attribute[str]("partition_key")

    index = Index.lsi("IndexName", attribute)

    # then
    assert isinstance(index, Index)
    assert str(index) == "LSI@IndexName(partition_key)"


def test_can_create_pk() -> None:
    # given
    index = Index.pk("partition_key")

    # then
    assert isinstance(index, Index)
    assert index.name == "#"
    assert index.index_type == Index.PRIMARY_KEY
    assert index.partition_key == "partition_key"
    assert str(index) == "#PK(partition_key)"


def test_can_create_gsi() -> None:
    # given
    index = Index.gsi("GSIIndex", "partition_key")

    # then
    assert isinstance(index, Index)
    assert index.name == "GSIIndex"
    assert index.index_type == Index.GLOBAL_INDEX
    assert index.partition_key == "partition_key"
    assert str(index) == "GSI@GSIIndex(partition_key)"


def test_can_create_lsi() -> None:
    # given
    index = Index.lsi("IndexName", "partition_key", "sort_key")

    # then
    assert isinstance(index, Index)
    assert index.name == "IndexName"
    assert index.index_type == Index.LOCAL_INDEX
    assert index.partition_key == "partition_key"
    assert index.sort_key == "sort_key"
    assert str(index) == "LSI@IndexName(partition_key, sort_key)"


def test_can_cast_to_dict() -> None:
    # given
    index = Index.lsi("IndexName", "partition_key", "sort_key")

    # when
    result = index.as_dict()

    # then
    assert result == {
        "IndexName": "IndexName",
        "KeySchema": [
            {"AttributeName": "partition_key", "KeyType": "HASH"},
            {"AttributeName": "sort_key", "KeyType": "RANGE"},
        ],
        "Projection": {
            "ProjectionType": "ALL"
        }
    }
