from src.utils import (get_value, is_empty, update_if_not_empty,
                       update_key_if_not_empty)


def test_is_empty():
    assert is_empty("")
    assert is_empty(" ")
    assert is_empty("  ")
    assert is_empty(None)
    assert not is_empty("Hello")

def test_update_if_not_empty():
    assert update_if_not_empty({}, "key", "value") == {"key": "value"}
    assert update_if_not_empty({}, "key", "") == {}
    assert update_if_not_empty({"key": "old_value"}, "key", "new_value") == {"key": "new_value"}

def test_update_key_if_not_empty():
    assert update_key_if_not_empty({"key": "value"}, {}, "key") == {"key": "value"}
    assert update_key_if_not_empty({"key": ""}, {}, "key") == {}
    assert update_key_if_not_empty({}, {}, "key") == {}

def test_get_value():
    assert get_value({"key": "value"}, None, "key") == "value"
    assert get_value({"key": "value"}, None, "non_existent_key") is None
    assert get_value({"key": {"nested_key": "nested_value"}}, None, "key", "nested_key") == "nested_value"