"""Test datastructures."""

import logging
import os
import tempfile

from async_bakalari_api.bakalari import Credentials, Schools
from async_bakalari_api.datastructure import UniqueTowns
import orjson
import pytest

data = '[{"name": "test_name","api_point": "test_api_point","town": "test_town"}]'


@pytest.mark.asyncio
async def test_school_list_from_file():
    """Test loading schools from file."""
    schools = Schools()
    schools.append_school("test_name", "test_api_point", "test_town")

    with tempfile.NamedTemporaryFile(delete=False) as file:
        file.write(orjson.dumps(schools.school_list))
        path = file.name
    try:
        schools: Schools | bool = await Schools().load_from_file(path)
        assert isinstance(schools, Schools)
        assert len(schools) == 1
        assert schools.school_list[0].name == "test_name"
        assert schools.school_list[0].api_point == "test_api_point"
        assert schools.school_list[0].town == "test_town"

    finally:
        os.remove(path)


@pytest.mark.asyncio
async def test_file_bad_data(caplog):
    """Mock file for testing."""

    caplog.set_level(logging.ERROR, logger="async_bakalari_api.datastructure")

    with tempfile.NamedTemporaryFile(delete=False) as file:
        file.write(b'{"broken": 1')  # non valid JSON format
        path = file.name
        file.close()
    try:
        schools = await Schools().load_from_file(path)
        assert schools is False
        assert any(
            "Unable to decode JSON file" in r.getMessage()
            for r in caplog.records
            if r.name == "async_bakalari_api.datastructure"
        )
    finally:
        os.remove(path)


async def test_schools_list_from_file_no_file():
    """Test loading schools from file."""

    schools: Schools | bool = await Schools().load_from_file("")
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
    test_town_no_town = schools.get_schools_by_town()

    assert len(schools.school_list) == 2
    assert len(test_town_in) == 1
    assert test_town_in[0].name == "test_school"
    assert len(test_town_out) == 0

    assert len(test_town_no_town) == 2


async def test_school_by_api_point():
    """Test getting schools by api point."""

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")

    test_api_point = schools.get_school_name_by_api_point("test_api_point_in")
    test_non_exist = schools.get_school_name_by_api_point("non_existing_api_point")

    assert len(schools.school_list) == 1
    assert test_api_point == "test_school"
    assert test_non_exist is False


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


@pytest.mark.asyncio
async def test_write_file():
    """Test writing to file."""

    schools = Schools()
    schools.append_school("test_school", "test_api_point_in", "test_town_in")
    schools.append_school("test_school2", "test_api_point_2", "test_town_2")

    expected = [
        {
            "name": "test_school",
            "api_point": "test_api_point_in",
            "town": "test_town_in",
        },
        {
            "name": "test_school2",
            "api_point": "test_api_point_2",
            "town": "test_town_2",
        },
    ]

    fd, path = tempfile.mkstemp()
    os.close(fd)

    try:
        assert await schools.save_to_file(path) is True

        with open(path, "rb") as f:
            data = orjson.loads(f.read())

        assert data == expected
    finally:
        os.remove(path)


@pytest.mark.asyncio
async def test_write_file_non_existent_file(caplog, monkeypatch):
    """Test write file failed."""

    caplog.set_level(logging.ERROR)

    schools = Schools()

    try:
        assert await schools.save_to_file("") is False
        assert any(
            "Unable to save schools list" in r.getMessage()
            for r in caplog.records
            if r.name == "async_bakalari_api.datastructure"
        )
    finally:
        return


@pytest.mark.asyncio
async def test_write_file_with_bad_data(caplog, monkeypatch):
    """Test write file failed with bad data."""
    schools = Schools()
    schools.append_school("a", "b", "c")

    caplog.set_level(
        logging.DEBUG,
    )

    def boom(*args, **kwargs):
        """Boom."""
        raise orjson.JSONEncodeError("bad", 0)

    monkeypatch.setattr(
        "async_bakalari_api.datastructure.orjson.dumps", boom, raising=True
    )

    fd, name = tempfile.mkstemp()
    os.close(fd)

    try:
        assert await schools.save_to_file(name) is False
        assert any(
            "Unable to encode JSON format while saving schools list to file"
            in r.getMessage()
            for r in caplog.records
            if r.name == "async_bakalari_api.datastructure"
        )
    finally:
        os.remove(name)


def test_credentials():
    """Test credentials datastructure."""

    data_json = {
        "user_id": "test_user_id",
        "access_token": "test_token",
        "refresh_token": "test_refresh_token",
        "username": "test_username",
    }

    credentials = Credentials.create_from_json(data_json)

    assert isinstance(credentials, Credentials)
    assert credentials.access_token == "test_token"
    assert credentials.refresh_token == "test_refresh_token"
    assert credentials.user_id == "test_user_id"
    assert credentials.username == "test_username"


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
