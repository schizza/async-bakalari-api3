"""Module contains test cases for the EndPoint class in the bakalari_api.const module."""

from src.bakalari_api.const import EndPoint


def test_Endpoint_get():
    """Test the get method of the EndPoint class."""

    truevalue = EndPoint.LOGIN.get("endpoint")
    assert truevalue == "/api/login"

    error_value = EndPoint.LOGIN.get("bad_key")
    assert not error_value
