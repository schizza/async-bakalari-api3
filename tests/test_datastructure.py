"""Test datastructures."""

import tempfile
from unittest.mock import patch

from src.bakalari_api.bakalari import Credentials, Schools
import orjson
import pytest


@pytest.fixture
def mocker_file(mocker):
    data = b'[{"name": "test_name","api_point": "test_api_point","town": "test_town"}]'
    mocked_file = mocker.mock_open(read_data=data)
    mocker.patch("builtins.open", mocked_file)


@pytest.mark.asyncio
async def test_school_list_from_file(mocker_file):

    schools: Schools = await Schools().load_from_file("fakefile")
    assert isinstance(schools, Schools)


@pytest.fixture
def mocker_file_bad_data(mocker):
    data = b'[{"name": "test_name","api_point": "test_api_point","town": "test_town"}'
    mocked_file = mocker.mock_open(read_data=data)
    mocker.patch("builtins.open", mocked_file)


@pytest.mark.asyncio
async def test_school_list_from_file_bad_data(mocker_file_bad_data):

    schools: Schools = await Schools().load_from_file("fakefile")
    assert not isinstance(schools, Schools)


@pytest.mark.asyncio
async def test_schools_list_from_file_no_file():

    schools: Schools = await Schools().load_from_file("")
    assert schools == False


@pytest.mark.asyncio
async def test_school_append():

    schools = Schools()

    assert not schools.append_school("", "test_api_point", "test_town_in")
    assert not schools.append_school("test_school", "", "test_town_in")
    assert not schools.append_school("test_school", "test_api_point", "")
    assert schools.append_school("test_school", "test_api_point", "test_town_in")


@pytest.mark.asyncio
async def test_school_by_name():

    schools = Schools()
    schools.append_school("test_school", "test_api_point", "test_town_in")
    schools.append_school("test_school_2", "test_api_point", "test_town_another_town")

    test_town_in = schools.get_schools_by_town("test_town_in")
    test_town_out = schools.get_schools_by_town("test_town_out")

    assert len(schools.school_list) == 2
    assert len(test_town_in) == 1
    assert test_town_in[0].name == "test_school"
    assert len(test_town_out) == 0


@pytest.mark.asyncio
async def test_school_by_api_point():

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")

    test_api_point = schools.get_school_name_by_api_point("test_api_point_in")
    test_non_exist = schools.get_school_name_by_api_point("non_existing_api_point")

    assert len(schools.school_list) == 1
    assert test_api_point == "test_school"
    assert test_non_exist == False


@pytest.mark.asyncio
async def test_get_url():

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")
    schools.append_school("test_school2", "test_api_point_out", "test_town_in")

    false_name_test = schools.get_url("not in")
    true_name_test = schools.get_url("test_school")
    both_specified = schools.get_url("test_school", 1)
    index_error = schools.get_url(idx=10)
    index = schools.get_url(idx=0)

    assert not false_name_test
    assert true_name_test == "test_api_point_in"
    assert not both_specified
    assert not index_error
    assert index == "test_api_point_in"


def open_err(*args, **kwargs):
    raise OSError


@pytest.mark.asyncio
async def test_write_file(monkeypatch):

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")
    schools.append_school("test_school2", "test_api_point_out", "test_town_in")

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = temp_dir + "test_data"
        schools.save_to_file(filename=filename)

        with open(filename, "+rb") as file:
            data = orjson.loads(file.read())
            file.close()

    assert orjson.dumps(data) == orjson.dumps(schools.school_list)

    with tempfile.TemporaryDirectory() as temp_dir:
        filename = temp_dir

        with patch("builtins.open", open_err):
            school = schools.save_to_file(filename=filename)
            assert not school


def test_credentials():

    data_json = {
        "user_id": "test_user_id",
        "access_token": "test_token",
        "refresh_token": "test_refresh_token",
    }

    credentials = Credentials.create_from_json(data_json)

    assert isinstance(credentials, Credentials)
    assert credentials.access_token == "test_token"
    assert credentials.refresh_token == "test_refresh_token"
    assert credentials.user_id == "test_user_id"
