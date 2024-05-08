import re
from unittest.mock import patch

import aiohttp
from aiohttp import hdrs
from aioresponses import aioresponses
from src.bakalari_api.bakalari import Bakalari, Schools, Credentials
from src.bakalari_api.const import EndPoint, Errors
from src.bakalari_api.exceptions import Ex
import pytest
import tempfile
import orjson

fs = "http://fake_server"


async def test_unauth_request():

    bakalari = Bakalari("http://fake_server")

    with aioresponses() as m:
        m.post(
            "http://fake_server" + EndPoint.KOMENS_UNREAD_COUNT.get("endpoint"),
            payload={"data": "we have data!"},
            headers={},
            status=200,
        )
        # we tries to `GET` response on `POST` method
        m.get(
            "http://fake_server" + EndPoint.KOMENS_UNREAD_COUNT.get("endpoint"),
            payload={"data": "we should have no data!"},
            headers={},
            status=200,
        )

        result = await bakalari.send_unauth_request(EndPoint.KOMENS_UNREAD_COUNT)
        assert result == {"data": "we have data!"}

        with pytest.raises(Ex.BadRequestException) as ex:
            result = await bakalari.send_unauth_request(EndPoint.KOMENS_UNREAD_COUNT)

        assert "Connection error:" in str(ex.value)

    # Bad server URL
    bakalari = Bakalari()
    m.get(
        EndPoint.KOMENS_UNREAD_COUNT.get("endpoint"),
        payload={"data": "we have data!"},
        headers={},
        status=200,
    )

    with pytest.raises(Ex.BadEndpointUrl) as ex:
        result = await bakalari.send_unauth_request(EndPoint.KOMENS_UNREAD_COUNT)


def test_get_request_url():

    bakalari = Bakalari()

    with pytest.raises(Ex.BadEndpointUrl) as ex:
        final_url = bakalari.get_request_url(EndPoint.LOGIN)

    assert "Bad endpoint url" in str(ex.value)

    bakalari.server = "http://fake_server"
    final_url = bakalari.get_request_url(EndPoint.LOGIN)
    assert final_url == "http://fake_server/api/login"


async def test_school_list():
    bakalari = Bakalari()
    pattern = re.compile(r"^https://sluzby\.bakalari\.cz/.*$")

    with aioresponses() as m:
        m.get(
            pattern,
            headers={"Accept": "application/json"},
            body="""[{"name": "town_name.a","schoolCount": 1},{"name":""}]""",
            status=200,
        )

        m.get(
            pattern,
            headers={"Accept": "application/json"},
            body="""{"name": "town_name", "schools": [{"name": "school_name","schoolUrl": "endpoint_url"}]}""",
        )

        result = await bakalari.async_schools_list()
        assert isinstance(result, Schools)
        assert result.get_url("school_name") == "endpoint_url"
        assert result.get_school_name_by_api_point("endpoint_url") == "school_name"
        assert isinstance(result.get_schools_by_town("town_name"), list)

        m.post(
            pattern,
            headers={"Accept": "application/json"},
            body="""{"name": "town_name", "schools": [{"name": "school_name","schoolUrl": "endpoint_url"}]}""",
        )
        result = await bakalari.async_schools_list()
        assert not result


async def test__send_request_aioex(monkeypatch: pytest.MonkeyPatch):

    bakalari = Bakalari("fake_server")

    with (
        patch("asyncio.timeout", side_effect=TimeoutError),
        pytest.raises(Ex.TimeoutException) as ex,
    ):
        result = await bakalari._send_request("fake_server", hdrs.METH_GET, "")

    assert "Timeout occurred while connecting to server" in str(ex.value)

    with (
        patch("aiohttp.ClientSession.get", side_effect=aiohttp.ClientConnectionError),
        pytest.raises(Ex.BadRequestException) as ex,
    ):
        result = await bakalari._send_request("", hdrs.METH_GET, "")

    assert "Connection error:" in str(ex.value)


async def test_send_auth_request():

    cache_file = f"{tempfile.TemporaryDirectory()}/cache_file"

    bakalari = Bakalari(
        "http://fake_server", auto_cache_credentials=True, cache_filename=cache_file
    )

    with pytest.raises(Ex.TokenMissing):
        result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)

    bakalari.credentials.access_token = "access_token"
    bakalari.credentials.refresh_token = "refresh_token"

    # we have expired access token and valid refresh token, we are trying refreshing with token
    with aioresponses() as m:
        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={"WWW-Authenticate": Errors.ACCESS_TOKEN_EXPIRED},
            status=401,
        )
        m.get(
            fs + EndPoint.LOGIN.endpoint,
            payload={
                "bak:UserId": "fake_user_id",
                "access_token": "fake_access_token",
                "refresh_token": "fake_refresh_token",
                "username": "fake_username",
            },
            status=200,
        )

        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={},
            payload="we should have some data",
            status=200,
        )

        result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)
        assert result == "we should have some data"
        assert bakalari.credentials.username == "fake_username"
        assert bakalari.credentials.access_token == "fake_access_token"
        assert bakalari.credentials.refresh_token == "fake_refresh_token"
        assert bakalari.credentials.user_id == "fake_user_id"

    # we have expired refresh token and access token
    result = None
    with aioresponses() as m:
        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={"WWW-Authenticate": Errors.ACCESS_TOKEN_EXPIRED},
            status=401,
        )

        m.get(
            fs + EndPoint.LOGIN.endpoint,
            headers={"WWW-Authenticate": Errors.REFRESH_TOKEN_EXPIRED},
            payload={
                "bak:UserId": "fake_user_id_expired",
                "access_token": "fake_access_token_expired",
                "refresh_token": "fake_refresh_token_expired",
                "username": "fake_username_expired",
            },
            status=401,
        )
        with pytest.raises(Ex.RefreshTokenExpired):
            result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)

        assert not result
        assert bakalari.credentials.username != "fake_username_expired"
        assert bakalari.credentials.access_token != "fake_access_token_expired"
        assert bakalari.credentials.refresh_token != "fake_refresh_token_expired"
        assert bakalari.credentials.user_id != "fake_user_id_expired"

    # we have valid access token
    result = None
    with aioresponses() as m:
        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={},
            payload="we have valid access token",
            status=200,
        )

        result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)

        assert result == "we have valid access token"

    # another exception is raised while using access token
    result = None
    with aioresponses() as m:
        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={},
            payload="we should have no data",
            status=200,
            exception=TimeoutError,
        )
        with pytest.raises(Ex.TimeoutException):
            result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)
        assert result != "we should have no data"

    # another exception is raised while using refresh token
    result = None
    with aioresponses() as m:
        m.post(
            fs + EndPoint.KOMENS_UNREAD.endpoint,
            headers={"WWW-Authenticate": Errors.ACCESS_TOKEN_EXPIRED},
            payload="we should have no data",
            status=401,
        )
        m.get(
            fs + EndPoint.LOGIN.endpoint,
            headers={},
            payload="we should have no data",
            status=401,
            exception=TimeoutError,
        )

        with pytest.raises(Ex.TimeoutException):
            result = await bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)
        assert result != "we should have no data"


async def test__send_request():

    bakalari = Bakalari("fake_server")

    with aioresponses() as m:
        # 1 - ACCESS TOKEN EXPIRED
        m.get(
            "fake_server",
            payload={},
            headers={"WWW-Authenticate": Errors.ACCESS_TOKEN_EXPIRED},
            status=401,
        )

        # 2 - REFRESH TOKEN EXPIRED
        m.post(
            "fake_server",
            payload={},
            headers={"WWW-Authenticate": Errors.REFRESH_TOKEN_EXPIRED},
            status=401,
        )

        # 3 - BadRequest in Authentication
        m.get(
            "fake_server",
            payload={},
            headers={"": ""},
            status=401,
        )

        # 4 - INVALID METHOD
        m.get(
            "fake_server",
            payload={"error_uri": Errors.INVALID_METHOD},
            headers={},
            status=400,
        )

        # 5 - INVALID METHOD
        m.get(
            "fake_server",
            payload={"error_uri": Errors.INVALID_LOGIN},
            headers={},
            status=400,
        )

        # 6 - REFRESH TOKEN REDEEMD
        m.get(
            "fake_server",
            payload={"error_uri": Errors.REFRESH_TOKEN_REDEEMD},
            headers={},
            status=400,
        )

        # 7 - INVALID REFRESH TOKEN
        m.get(
            "fake_server",
            payload={"error_uri": Errors.INVALID_REFRESH_TOKEN},
            headers={},
            status=400,
        )

        # 8 - BadRequestExeption in 400
        m.get(
            "fake_server",
            payload={"other_exception": "another bad thing happened"},
            headers={},
            status=400,
        )

        # 9 - Pass valid data
        m.get(
            "fake_server",
            payload={"yupiee": "we have a data!"},
            headers={},
            status=200,
        )

        # 10 - Some weird things happening
        m.get(
            "fake_server",
            payload={"Oh god.": "We have some kind of 500 error."},
            headers={},
            status=500,
        )

        ###### TESTS  ####
        # 1
        with pytest.raises(Ex.AccessTokenExpired) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        # 2
        with pytest.raises(Ex.RefreshTokenExpired) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_POST, headers={}
            )
        # 3
        with pytest.raises(Ex.BadRequestException) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )

        # 4
        with pytest.raises(Ex.InvalidHTTPMethod) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        # 5
        with pytest.raises(Ex.InvalidLogin) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        # 6
        with pytest.raises(Ex.RefreshTokenRedeemd) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        # 7
        with pytest.raises(Ex.InvalidRefreshToken) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )

        # 8
        with pytest.raises(Ex.BadRequestException) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        assert "another bad thing happened" in str(exc.value)

        # 9
        response = await bakalari._send_request(
            "fake_server", hdrs.METH_GET, headers={}
        )
        assert response == {"yupiee": "we have a data!"}

        # 10
        with pytest.raises(Ex.BadRequestException) as exc:
            response = await bakalari._send_request(
                "fake_server", hdrs.METH_GET, headers={}
            )
        assert "We have some kind of 500 error." in str(exc.value)


def raise_OSError(*args, **kwargs):
    raise OSError


@pytest.fixture
def mocker_file(mocker):
    data = b'{"username": "test_name", "access_token": "test_access","refresh_token": "test_refresh", "user_id": "test_user_id"}'
    mocked_file = mocker.mock_open(read_data=data)
    mocker.patch("builtins.open", mocked_file)


def test_load_credentials_OSError():

    bakalari = Bakalari()

    # cannot open file
    with patch("builtins.open", raise_OSError):
        false_data = bakalari.load_credentials("fake_file")
        assert not false_data


def test_load_credentials_success(mocker_file):

    bakalari = Bakalari()

    success = bakalari.load_credentials("fake_file")
    assert success

    assert bakalari.credentials.username == "test_name"
    assert bakalari.credentials.access_token == "test_access"
    assert bakalari.credentials.refresh_token == "test_refresh"


def test_save_file_success():

    bakalari = Bakalari()
    bakalari.credentials = bakalari.credentials.create_from_json(
        {
            "username": "test_name",
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "user_id": "test_user_id",
        }
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = temp_dir + "test_data"
        bakalari.save_credentials(filename=filename)

        with open(filename, "+rb") as file:
            data = orjson.loads(file.read())
            file.close()

        assert data.get("username") == bakalari.credentials.username
        assert data.get("access_token") == bakalari.credentials.access_token
        assert data.get("refresh_token") == bakalari.credentials.refresh_token
        assert data.get("user_id") == bakalari.credentials.user_id

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = temp_dir

        with patch("builtins.open", raise_OSError):
            false = bakalari.save_credentials(filename=filename)
            assert not false


def test_save_file_cache_file():
    # we have auto_cache, but no filename provided.
    with pytest.raises(Ex.CacheError) as ex:
        bakalari = Bakalari("", auto_cache_credentials=True, cache_filename=None)
    assert "Auto-cache is enabled, but no filename is provided!" in str(ex.value)

    bakalari = Bakalari("", auto_cache_credentials=True, cache_filename="fake_file")
    bakalari.credentials = bakalari.credentials.create_from_json(
        {
            "username": "test_name",
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "user_id": "test_user_id",
        }
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = temp_dir + "test_data"
        bakalari.cache_filename = filename
        bakalari.save_credentials()

        with open(filename, "+rb") as file:
            data = orjson.loads(file.read())
            file.close()

        assert data.get("username") == bakalari.credentials.username
        assert data.get("access_token") == bakalari.credentials.access_token
        assert data.get("refresh_token") == bakalari.credentials.refresh_token
        assert data.get("user_id") == bakalari.credentials.user_id


async def test_first_login():

    filename = f"{tempfile.TemporaryDirectory()}/cache_file"
    bakalari = Bakalari(fs, auto_cache_credentials=True, cache_filename=filename)

    # we have valid username and password
    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.LOGIN.endpoint,
            headers={},
            payload={
                "bak:UserId": "fake_user_id",
                "username": "fake_user_name",
                "access_token": "fake_access_token",
                "token_type": "Bearer",
                "expires_in": 0,
                "scope": "offline_access bakalari_api",
                "refresh_token": "fake_refresh_token",
            },
            status=200,
        )

        result = await bakalari.first_login("username", "password")
        assert isinstance(result, Credentials)
        assert bakalari.credentials.access_token == "fake_access_token"
        assert bakalari.credentials.refresh_token == "fake_refresh_token"

    # we don't have valid username / password provided
    # we have valid username and password
    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.LOGIN.endpoint,
            headers={},
            payload={"error_uri": Errors.INVALID_LOGIN},
            status=400,
        )
        with pytest.raises(Ex.InvalidLogin) as ex:
            result = await bakalari.first_login("username", "password")

        assert "Invalid login!" in str(ex.value)
