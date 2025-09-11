"""Tests for new features."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from src.bakalari_api import Bakalari


@pytest.mark.asyncio
async def test_get_grades():
    """Test get_grades."""
    with aioresponses() as m:
        m.get(
            "https://bakalari.example.com/api/3/marks",
            payload={
                "Subjects": [
                    {
                        "Subject": {"Id": "1", "Name": "Math", "Abbrev": "M"},
                        "Marks": [
                            {
                                "Caption": "Test",
                                "MarkText": "1",
                                "Vaha": "50",
                                "Date": "2025-01-01",
                                "Description": "Final exam",
                            }
                        ],
                    }
                ]
            },
        )
        bakalari = Bakalari(server="https://bakalari.example.com")
        bakalari.credentials.access_token = "test"
        grades = await bakalari.get_grades()
        assert grades is not None
        assert len(grades.grades) == 1
        assert grades.grades[0].subject.name == "Math"


@pytest.mark.asyncio
async def test_get_timetable():
    """Test get_timetable."""
    with aioresponses() as m:
        m.get(
            "https://bakalari.example.com/api/3/timetable/actual",
            payload={
                "Days": [
                    {
                        "Date": "2025-01-01",
                        "Hours": [
                            {
                                "Subject": {"Id": "1", "Name": "Math", "Abbrev": "M"},
                                "Teacher": {"Name": "Mr. Smith"},
                                "Room": {"Name": "Room 101"},
                                "Group": {"Name": "Group A"},
                                "BeginTime": "08:00",
                                "EndTime": "08:45",
                            }
                        ],
                    }
                ]
            },
        )
        bakalari = Bakalari(server="https://bakalari.example.com")
        bakalari.credentials.access_token = "test"
        timetable = await bakalari.get_timetable()
        assert timetable is not None
        assert len(timetable.events) == 1
        assert timetable.events[0].subject.name == "Math"


@pytest.mark.asyncio
async def test_get_homework():
    """Test get_homework."""
    with aioresponses() as m:
        m.get(
            "https://bakalari.example.com/api/3/homeworks",
            payload={
                "Homeworks": [
                    {
                        "Subject": {"Id": "1", "Name": "Math", "Abbrev": "M"},
                        "DateStart": "2025-01-01",
                        "DateEnd": "2025-01-08",
                        "Content": "Do the math.",
                        "Done": False,
                    }
                ]
            },
        )
        bakalari = Bakalari(server="https://bakalari.example.com")
        bakalari.credentials.access_token = "test"
        homework = await bakalari.get_homework()
        assert homework is not None
        assert len(homework) == 1
        assert homework[0].subject.name == "Math"
