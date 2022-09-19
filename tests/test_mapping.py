import pytest

from amano import Item, Mapping


@pytest.mark.parametrize(
    "given, expected",
    [
        ["a", "a"],
        ["a_b_c", "a_b_c"],
        ["a_BC", "a_BC"],
        ["", ""],
    ],
)
def test_pass_through_mapping(given, expected) -> None:
    mapping = Mapping.PASS_THROUGH
    assert mapping[given] == expected


def test_pass_through_mapping_integration() -> None:
    # given
    class MyItem(Item, mapping=Mapping.PASS_THROUGH):
        a: str
        a_b_c: str
        a_BC: str

    # when
    instance = MyItem.hydrate(
        {"a": {"S": "a"}, "a_b_c": {"S": "b"}, "a_BC": {"S": "c"}}
    )

    # then
    assert instance.a == "a"
    assert instance.a_b_c == "b"
    assert instance.a_BC == "c"


@pytest.mark.parametrize(
    "given, expected",
    [
        ["a", "A"],
        ["a_b_c", "ABC"],
        ["a_BC", "ABC"],
        ["", ""],
    ],
)
def test_pascal_case_mapping(given, expected) -> None:
    mapping = Mapping.PASCAL_CASE
    assert mapping[given] == expected, f"Failed for {given}"


def test_pascal_case_mapping_integration() -> None:
    # given
    class MyItem(Item, mapping=Mapping.PASCAL_CASE):
        a: str
        a_b_c: str
        a_bcd: str

    # when
    instance = MyItem.hydrate(
        {"A": {"S": "a"}, "ABC": {"S": "b"}, "ABcd": {"S": "c"}}
    )

    # then
    assert instance.a == "a"
    assert instance.a_b_c == "b"
    assert instance.a_bcd == "c"

    # when
    data = instance.extract()

    # then
    assert data == {"A": {"S": "a"}, "ABC": {"S": "b"}, "ABcd": {"S": "c"}}


@pytest.mark.parametrize(
    "given, expected",
    [
        ["a", "a"],
        ["a_b_c", "aBC"],
        ["a_BC", "aBc"],
        ["", ""],
    ],
)
def test_camel_case_mapping(given, expected) -> None:
    mapping = Mapping.CAMEL_CASE
    assert mapping[given] == expected, f"Failed for {given}"


def test_camel_case_mapping_integration() -> None:
    # given
    class MyItem(Item, mapping=Mapping.CAMEL_CASE):
        a: str
        a_b_c: str
        a_bc_d: str

    # when
    instance = MyItem.hydrate(
        {"a": {"S": "a"}, "aBC": {"S": "b"}, "aBcD": {"S": "c"}}
    )

    # then
    assert instance.a == "a"
    assert instance.a_b_c == "b"
    assert instance.a_bc_d == "c"

    # when
    data = instance.extract()

    # then
    assert data == {"a": {"S": "a"}, "aBC": {"S": "b"}, "aBcD": {"S": "c"}}
