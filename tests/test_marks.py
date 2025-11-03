"""Integration tests for the marks service layer."""

from __future__ import annotations

import datetime as dt
import asyncio
import logging

import pytest

from src.async_bakalari_api.const import EndPoint
from src.async_bakalari_api.marks import Marks
from src.async_bakalari_api.marks_models import FlatSnapshot, Subject

FS = "http://fake_server"


def _payload_marks() -> dict[str, object]:
    return {
        "MarkOptions": [
            {"Id": "1", "Abbrev": "1", "Name": "Jedna"},
            {"Id": "A", "Abbrev": "A", "Name": "Áčko"},
        ],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.5",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "m1",
                        "MarkDate": "2024-01-01T12:00:00+00:00",
                        "Caption": "Písemka 1",
                        "Theme": "Lineární rovnice\n",
                        "MarkText": "1",
                        "Teacher": "Učitel A",
                        "SubjectId": "101",
                        "IsNew": True,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    },
                    {
                        "Id": "m2",
                        "MarkDate": "2024-01-05T08:00:00+00:00",
                        "Caption": "Písemka 2",
                        "Theme": "Funkce",
                        "MarkText": "A",
                        "Teacher": "Učitel A",
                        "SubjectId": "101",
                        "IsNew": False,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    },
                ],
            },
            {
                "Subject": {"Id": "202", "Abbrev": "AJ", "Name": "Angličtina"},
                "AverageText": "2.0",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "m3",
                        "MarkDate": "2024-01-03T07:30:00+00:00",
                        "Caption": "Vocabulary",
                        "Theme": "Unit 1",
                        "MarkText": "X",  # not present in MarkOptions -> placeholder
                        "Teacher": "Učitel B",
                        "SubjectId": "202",
                        "IsNew": True,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    }
                ],
            },
        ],
    }


class DummyBakalari:
    """Minimal fake implementing send_auth_request."""

    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    async def send_auth_request(self, endpoint: EndPoint) -> dict[str, object]:
        assert endpoint is EndPoint.MARKS
        return self.payload


async def _prepare_marks_instance(payload: dict[str, object] | None = None) -> Marks:
    data = payload or _payload_marks()
    marks = Marks(DummyBakalari(data))
    await marks.fetch_marks()
    return marks


def run(coro):
    return asyncio.run(coro)


def test_fetch_populates_dataset_and_grouping():
    marks = run(_prepare_marks_instance())

    subjects = run(marks.get_subjects())
    assert {s.id for s in subjects} == {"101", "202"}

    mat_marks = run(marks.get_marks_by_subject("101"))
    assert [m.id for m in mat_marks] == ["m1", "m2"]

    groups = run(marks.get_marks_all())
    assert {subject.id for subject in groups} == {"101", "202"}
    assert all(isinstance(subject, Subject) for subject in groups)

    mat_group = next(subject for subject in groups if subject.id == "101")
    assert [m.id for m in mat_group.marks] == ["m1", "m2"]

    subjects_map = marks.get_subjects_map()
    assert subjects_map["202"].abbr == "AJ"


def test_get_new_marks_by_date_filters():
    marks = run(_prepare_marks_instance())

    day = dt.datetime(2024, 1, 1)
    result = run(marks.get_new_marks_by_date(date_from=day, date_to=day))
    assert [subject.id for subject in result] == ["101"]
    assert [mark.id for mark in result[0].marks] == ["m1"]

    range_from = dt.datetime(2024, 1, 2)
    range_to = dt.datetime(2024, 1, 4)
    result = run(marks.get_new_marks_by_date(
        date_from=range_from, date_to=range_to, subject_id="202"
    ))
    assert [subject.id for subject in result] == ["202"]
    assert [mark.id for mark in result[0].marks] == ["m3"]


def test_snapshot_normalized_output_and_conversion():
    marks = run(_prepare_marks_instance())

    snapshot = run(marks.get_snapshot(order="asc"))
    assert isinstance(snapshot, FlatSnapshot)
    assert set(snapshot.subjects.keys()) == {"101", "202"}
    assert snapshot.marks_flat[0].id == "m1"  # asc -> oldest first

    snapshot_dict = run(marks.get_snapshot(to_dict=True, order="desc"))
    assert snapshot_dict["marks_flat"][0]["id"] == "m2"
    assert snapshot_dict["marks_grouped"]["202"][0]["mark_text"] == "X"


def test_format_and_flat_helpers():
    marks = run(_prepare_marks_instance())

    formatted = run(marks.format_all_marks())
    assert "Matematika (MAT)" in formatted
    assert "[2024-01-05] Písemka 2 -> Áčko" in formatted

    flat_desc = run(marks.get_flat(order="desc"))
    assert [mark.id for mark in flat_desc] == ["m2", "m3", "m1"]


def test_missing_markoptions_logs_warning(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.WARNING, logger="Bakalari API"):
        run(_prepare_marks_instance())

    assert any("MarkOptions not found" in record.message for record in caplog.records)


def test_unknown_subject_logs_warning(caplog: pytest.LogCaptureFixture):
    payload = {
        "MarkOptions": [{"Id": "1", "Abbrev": "1", "Name": "Jedna"}],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.0",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "mx",
                        "MarkDate": "2024-01-10T08:00:00+00:00",
                        "Caption": "Orphan mark",
                        "Theme": "",
                        "MarkText": "1",
                        "Teacher": "Učitel X",
                        "SubjectId": "999",
                        "IsNew": False,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    }
                ],
            }
        ],
    }

    with caplog.at_level(logging.WARNING, logger="Bakalari API"):
        marks = run(_prepare_marks_instance(payload=payload))

    assert any("Subject 999 not found" in record.message for record in caplog.records)
    assert run(marks.get_marks_all()) == []


def test_diff_ids_detection():
    marks = run(_prepare_marks_instance())

    previous = {"m1", "m2"}
    new_ids, new_items = run(marks.diff_ids(previous_ids=previous))
    assert new_ids == {"m3"}
    assert [item.id for item in new_items] == ["m3"]

