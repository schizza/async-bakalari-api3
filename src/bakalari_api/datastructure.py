"""Datastructure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import orjson

from .const import Token
from .logger_api import api_logger

log = api_logger("Bakalari API").get()


@dataclass
class Credentials:
    """Credentials holder."""

    username: str = None
    access_token: str = None
    refresh_token: str = None
    user_id: str = None

    @classmethod
    def create(cls, data: dict[str, Any]) -> Credentials:
        """Create class object form data."""

        return cls(
            user_id=data[Token.USER_ID],
            access_token=data[Token.ACCESS_TOKEN],
            refresh_token=data[Token.REFRESH_TOKEN],
        )

    @classmethod
    def create_from_json(cls, data: dict[str, Any]) -> Credentials:
        """Return class object from JSON dictionary."""
        return Credentials.create(
            {
                Token.USER_ID: data["user_id"],
                Token.ACCESS_TOKEN: data["access_token"],
                Token.REFRESH_TOKEN: data["refresh_token"],
            }
        )


@dataclass
class School:
    """Data structure for one school item."""

    name: str = None
    api_point: str = None
    town: str = None


class Schools:
    """List of schools with their url for Bakalari API."""

    def __init__(self) -> None:
        """List of schools with their url for Bakalari API."""

        self.school_list: list[School] = []

    def append_school(
        self,
        name: str,
        api_point: str,
        town: str,
    ) -> bool:
        """Append new school to the school_list list."""

        if name == "" or None:
            log.error(
                f"School's name should not be none or empty! (name={name}, api_point={api_point}, town={town})"
            )
            return False

        if api_point == "" or None:
            log.error(
                f"School's API point should not be none or empty! (name={name}, api_point={api_point}, town={town})"
            )
            return False

        if town == "" or None:
            log.error(
                f"School's town should not be none or empty! (name={name}, api_point={api_point}, town={town})"
            )
            return False

        new_school = School(name=name, api_point=api_point, town=town)
        self.school_list.append(new_school)

        return True

    def get_url(self, name: str | None = None, idx: int | None = None) -> str | False:
        """Return url for school from name or index in dictionary.

        Only one must be specified - name or index, otherwise returns False
        If name or index is not found in dictionary returns False.
        """

        if (name is not None) and (idx is not None):
            return False

        if name is not None:
            for item in self.school_list:
                if name in item.name:
                    return item.api_point

        if idx is not None:
            try:
                return self.school_list[idx].api_point
            except IndexError:
                return False

        return False

    def get_schools_by_town(self, town: str | None = None) -> list[School]:
        """Get list of schools in town."""
        _schools = []
        for item in self.school_list:
            _schools.append(item) if item.town in town else None
        return _schools

    def get_school_name_by_api_point(self, api_point: str) -> str | bool:
        """Get school name by its api point."""

        for item in self.school_list:
            if api_point == item.api_point:
                return item.name
        return False

    def save_to_file(self, filename: str) -> bool:
        """Save loaded school list to file in JSON format."""

        schools = []

        for item in self.school_list:
            new_data = {
                "name": item.name,
                "api_point": item.api_point,
                "town": item.town,
            }
            schools.append(new_data)

        try:
            with open(filename, "wb") as file:
                file.write(orjson.dumps(schools, option=orjson.OPT_INDENT_2))
            file.close()
        except OSError:
            return False

        return True

    async def load_from_file(self, filename: str) -> Schools:
        """Load schools list from a file."""

        try:
            with open(filename, mode="+rb") as file:
                data = orjson.loads(file.read())
            file.close()
        except OSError:
            return False
        except orjson.JSONDecodeError:
            log.error(f"Unable to decode JSON file. File {filename} is corrupted.")
            return False

        for item in data:
            self.append_school(
                item.get("name"), item.get("api_point"), item.get("town")
            )

        return self
