"""Test datastructures."""

import tempfile
from unittest.mock import patch

import orjson
import pytest
from src.bakalari_api.bakalari import Credentials, Schools
from src.bakalari_api.datastructure import UniqueTowns


@pytest.fixture
def mocker_file(mocker):
    """Mock file for testing."""
    data = b'[{"name": "test_name","api_point": "test_api_point","town": "test_town"}]'
    mocked_file = mocker.mock_open(read_data=data)
    mocker.patch("builtins.open", mocked_file)


async def test_school_list_from_file(mocker_file):
    """Test loading schools from file."""

    schools: Schools = await Schools().load_from_file("fakefile")
    assert isinstance(schools, Schools)


@pytest.fixture
def mocker_file_bad_data(mocker):
    """Mock file for testing."""

    data = b'[{"name": "test_name","api_point": "test_api_point","town": "test_town"}'
    mocked_file = mocker.mock_open(read_data=data)
    mocker.patch("builtins.open", mocked_file)


async def test_school_list_from_file_bad_data(mocker_file_bad_data):
    """Test loading schools from file."""

    schools: Schools = await Schools().load_from_file("fakefile")
    assert not isinstance(schools, Schools)


async def test_schools_list_from_file_no_file():
    """Test loading schools from file."""

    schools: Schools = await Schools().load_from_file("")
    assert schools is False


async def test_school_append():
    """Test appending schools to the list."""

    schools = Schools()

    assert not schools.append_school("", "test_api_point", "test_town_in")
    assert not schools.append_school("test_school", "", "test_town_in")
    assert not schools.append_school("test_school", "test_api_point", "")
    assert schools.append_school("test_school", "test_api_point", "test_town_in")
    assert len(schools) == 1


async def test_school_by_name():
    """Test getting schools by name."""

    schools = Schools()
    schools.append_school("test_school", "test_api_point", "test_town_in")
    schools.append_school("test_school_2", "test_api_point", "test_town_another_town")

    test_town_in = schools.get_schools_by_town("test_town_in")
    test_town_out = schools.get_schools_by_town("test_town_out")

    assert len(schools.school_list) == 2
    assert len(test_town_in) == 1
    assert test_town_in[0].name == "test_school"
    assert len(test_town_out) == 0


async def test_school_by_api_point():
    """Test getting schools by api point."""

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")

    test_api_point = schools.get_school_name_by_api_point("test_api_point_in")
    test_non_exist = schools.get_school_name_by_api_point("non_existing_api_point")

    assert len(schools.school_list) == 1
    assert test_api_point == "test_school"
    assert test_non_exist is None


async def test_get_url():
    """Test getting url by name or index."""

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
    """Raise OSError."""
    raise OSError


async def test_write_file(monkeypatch):
    """Test writing to file."""

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
    """Test credentials datastructure."""

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


def test_append_unique_town():
    """Test appending unique towns."""

    towns = UniqueTowns()
    towns.append("Town A")
    towns.append("Town B")
    towns.append("Town C")
    assert len(towns) == 3
    assert "Town A" in towns
    assert "Town B" in towns
    assert "Town C" in towns


def test_append_duplicate_town():
    """Test appending duplicate towns."""
    towns = UniqueTowns()
    towns.append("Town A")
    towns.append("Town B")
    towns.append("Town A")
    assert len(towns) == 2
    assert "Town A" in towns
    assert "Town B" in towns


def test_remove_town():
    """Test removing town."""

    towns = UniqueTowns()
    towns.append("Town A")
    towns.append("Town B")
    towns.append("Town C")
    assert len(towns) == 3
    del towns["Town B"]
    assert len(towns) == 2
    assert "Town A" in towns
    assert "Town B" not in towns
    assert "Town C" in towns


def test_get_town_by_index():
    """Test getting town by index."""
    towns = UniqueTowns()
    towns.append("Town A")
    towns.append("Town B")
    towns.append("Town C")
    assert towns[0] == "Town A"
    assert towns[1] == "Town B"
    assert towns[2] == "Town C"


def test_get_all_towns():
    """Test getting all towns."""

    towns = Schools()
    towns.towns_list.append("Town A")
    towns.towns_list.append("Town B")
    towns.towns_list.append("Town C")
    assert towns.get_all_towns() == ["Town A", "Town B", "Town C"]


def test_iterate_towns():
    """Test iterating over towns."""
    towns = UniqueTowns()
    towns.append("Town A")
    towns.append("Town B")
    towns.append("Town C")
    assert list(towns) == ["Town A", "Town B", "Town C"]


def test_count_towns():
    """Test counting towns."""
    towns = Schools()
    towns.towns_list.append("Town A")
    towns.towns_list.append("Town B")
    towns.towns_list.append("Town C")
    assert towns.count_towns() == 3


def test_str_towns():
    """Test counting towns."""
    towns = Schools()
    towns.towns_list.append("Town A")
    assert str(towns.towns_list) == "['Town A']"


def test_istown():
    """Test checking if town is in the list."""
    towns = Schools()
    towns.towns_list.append("Town A")
    assert towns.istown("Town A")


def test_get_towns_partial_name():
    """Test getting towns by partial name."""
    towns = Schools()
    towns.towns_list.append("Town A")
    towns.towns_list.append("Town B")
    towns.towns_list.append("Town C")
    assert towns.get_towns_partial_name("own") == ["Town A", "Town B", "Town C"]
    assert towns.get_towns_partial_name("own A") == ["Town A"]
