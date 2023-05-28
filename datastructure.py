"""Datastructure."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass

import orjson

from const import Token


@dataclass
class Credentials:
    """Credentials holder."""

    username: str = None
    access_token: str = None
    refresh_token: str = None
    user_id: str = None

    @classmethod
    def get(cls, data: dict[str, Any]) -> Credentials:
        """ "Return class object."""
        return cls(
            user_id=data[Token.USER_ID],
            access_token=data[Token.ACCESS_TOKEN],
            refresh_token=data[Token.REFRESH_TOKEN],
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
        self.school_list: list[School] = []

    def append_school(
        self, name: str = None, api_point: str = None, town: str = None
    ) -> None:
        """Append new school to the list."""

        new_school = School(name=name, api_point=api_point, town=town)
        self.school_list.append(new_school)

    def get_url(self, name: str | None = None, idx: int | None = None) -> str | False:
        """Returns url for school from name or index in dictionary.
        Only one must be specified - name or index, otherwise returns False

        If name or index is not found in dictionary returns False."""

        if (name is not None) and (idx is not None):
            return False

        if name is not None:
            for item in self.school_list:
                if name in item.name:
                    return item.api_point

        if idx is not None:
            return self.school_list[idx].api_point

        return False

    def get_schools_by_town(self, town: str = None) -> list[School]:
        """Get list of schools in town.

        Returns list of School obj."""
        _schools = []
        for item in self.school_list:
            if town in item.town:
                _schools.append(item)
        return _schools

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

    def load_from_file(self, filename: str) -> Schools:
        """Loads schools list from a file.

        Returns Schools obj."""

        try:
            with open(filename, mode="+rb") as file:
                data = orjson.loads(file.read())
            file.close()
        except OSError:
            return False

        for item in data:
            self.append_school(
                item.get("name"), item.get("api_point"), item.get("town")
            )

        return self
