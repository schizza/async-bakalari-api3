from bakalari_api.const import EndPoint


def test_Endpoint_get():

    truevalue = EndPoint.LOGIN.get("endpoint")
    assert truevalue == "/api/login"

    error_value = EndPoint.LOGIN.get("bad_key")
    assert not error_value
