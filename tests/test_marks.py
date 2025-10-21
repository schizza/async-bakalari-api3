"""Tests for Marks module."""

import datetime as dt
import logging

from src.async_bakalari_api.datastructure import Credentials
import pytest
from aioresponses import aioresponses

from src.async_bakalari_api.bakalari import Bakalari
from src.async_bakalari_api.const import EndPoint
from src.async_bakalari_api.marks import Marks

fs = "http://fake_server"

cred: Credentials = Credentials(access_token="token", refresh_token="refresh_token")


def _payload_marks():
    """Return a synthetic payload for EndPoint.MARKS."""
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
                        "MarkText": "X",  # not present in MarkOptions -> triggers placeholder + warning
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


async def _prepare_marks_instance(payload=None) -> Marks:
    """Create a Bakalari + Marks instance and feed fixtures via mocked API."""
    bakalari = Bakalari(fs, credentials=cred)
    marks = Marks(bakalari)
    # authorize

    data = payload or _payload_marks()

    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.MARKS.get("endpoint"),
            payload=data,
            headers={},
            status=200,
        )
        await marks.fetch_marks()

    await bakalari.__aexit__()

    return marks


async def test_marks_fetch_and_grouping():
    """Marks.fetch_marks populates subjects and marks; grouping works via get_marks_all."""
    marks = await _prepare_marks_instance()

    subjects = await marks.get_subjects()
    assert isinstance(subjects, list)
    assert len(subjects) == 2

    # Per-subject marks
    mat_marks = await marks.get_marks_by_subject("101")
    aj_marks = await marks.get_marks_by_subject("202")
    assert len(mat_marks) == 2
    assert len(aj_marks) == 1

    # Grouped view (all marks)
    groups = await marks.get_marks_all()
    # two subjects with at least one mark each
    assert len(groups) == 2
    # identifiers and some sanity
    ids = {s.id for s in groups}
    assert {"101", "202"}.issubset(ids)

    # Check that all_marks_for_subjects is a list of SubjectsBase objects
    # and that holds just marks for subject with id "101"
    all_marks_for_subjects = await marks.get_marks_all(subject_id="101")
    assert len(all_marks_for_subjects) == 1
    assert (
        all_marks_for_subjects.__repr__()
        == "[<SubjectsBase id=101 abbr=MAT name=Matematika>]"
    )

    # Empty list for unknown subject
    assert await marks.get_marks_all(subject_id="999") == []

    # Check that unknown mark option produced placeholder text (equals raw MarkText)
    # We expect the AJ mark to have marktext.text == "X"
    aj_group = next(g for g in groups if g.id == "202")
    assert len(list(aj_group.marks)) == 1
    mark = list(aj_group.marks)[0]
    assert mark.marktext is not None
    assert mark.marktext.text == "X"

    # Check __repr__ of SubjectBase
    assert (
        subjects.__repr__()
        == "[<SubjectsBase id=101 abbr=MAT name=Matematika>, <SubjectsBase id=202 abbr=AJ name=Angličtina>]"
    )

    # Check __str__ of SubjectBase
    assert (
        subjects[0].__str__()
        == f"name: Matematika\nid: 101\nabbr: MAT\nAverage: 1.5\npoints_only: False\n----\n"
    )

    # Check SubjectRegistry
    assert (
        marks.subjects.__repr__()
        == "<SubjectsRegistry (id='101', abbr='MAT', name='Matematika'), (id='202', abbr='AJ', name='Angličtina')>"
    )

    assert (
        "202 abbr: AJ name: Angličtina average_text: 2.0 points_only: False"
        in marks.subjects.__str__()
    )
    assert (
        "101 abbr: MAT name: Matematika average_text: 1.5 points_only: False"
        in marks.subjects.__str__()
    )

    assert "subject_id: 101" in marks.subjects.get_marks("101").__str__()
    assert "subject_id: 202" in marks.subjects.get_marks("202").__str__()
    assert "subject_id: 202" not in marks.subjects.get_marks("101").__str__()

    formatted = mat_marks[0].__str__()

    assert "id: m1" in formatted


async def test_marks_new_and_date_filters():
    """Test new marks and date range filters."""
    marks = await _prepare_marks_instance()

    # All new marks (is_new=True): m1 (MAT) + m3 (AJ) => grouped by subjects => 2 groups
    new_grouped = await marks.get_new_marks()
    assert len(new_grouped) == 2
    ids = {s.id for s in new_grouped}
    assert {"101", "202"}.issubset(ids)

    # By date - one day containing only m1 (2024-01-01)
    by_day = await marks.get_new_marks_by_date(date=dt.datetime(2024, 1, 1))
    # only MAT group present, because AJ's m3 is on 2024-01-03
    assert len(by_day) == 1
    assert by_day[0].id == "101"
    assert len(list(by_day[0].marks)) == 1
    assert list(by_day[0].marks)[0].id == "m1"

    # By range 2024-01-01 to 2024-01-02: only m1
    by_range = await marks.get_new_marks_by_date(
        date=dt.datetime(2024, 1, 1), date_to=dt.datetime(2024, 1, 2)
    )
    assert len(by_range) == 1
    assert by_range[0].id == "101"
    assert len(list(by_range[0].marks)) == 1
    assert list(by_range[0].marks)[0].id == "m1"

    # Only for specific subject in a range
    by_subject = await marks.get_new_marks_by_date(
        date=dt.datetime(2024, 1, 2), date_to=dt.datetime(2024, 1, 4), subject_id="202"
    )
    # AJ only, with m3
    assert len(by_subject) == 1
    assert by_subject[0].id == "202"
    assert len(list(by_subject[0].marks)) == 1
    assert list(by_subject[0].marks)[0].id == "m3"

    by_subject_non_exist = await marks.get_new_marks_by_date(
        date=dt.datetime(2024, 1, 2), date_to=dt.datetime(2024, 1, 4), subject_id="999"
    )
    assert len(by_subject_non_exist) == 0

    # get_marks_all filter: single day containing m2 only (2024-01-05)
    all_day = await marks.get_marks_all(date=dt.datetime(2024, 1, 5))
    assert len(all_day) == 1
    assert all_day[0].id == "101"
    mm = list(all_day[0].marks)
    assert len(mm) == 1 and mm[0].id == "m2"

    # get_marks_all filter: single day, specified with subjectcontaining m2 only (2024-01-05)
    all_day = await marks.get_marks_all(subject_id="101", date=dt.datetime(2024, 1, 5))
    assert len(all_day) == 1
    assert all_day[0].id == "101"
    mm = list(all_day[0].marks)
    assert len(mm) == 1 and mm[0].id == "m2"


async def test_format_and_print_all_marks(capsys):
    """Test formatted output and printing helpers."""
    marks = await _prepare_marks_instance()

    formatted = await marks.format_all_marks()

    # headers and some content present
    assert "Matematika (MAT) | average: 1.5" in formatted
    assert "Angličtina (AJ) | average: 2.0" in formatted
    # contains lines with dates and captions
    assert "[2024-01-01] Písemka 1 -> Jedna [NEW]" in formatted
    assert "[2024-01-05] Písemka 2 -> Áčko" in formatted
    # placeholder "X" appears for AJ mark
    assert "[2024-01-03] Vocabulary -> X" in formatted


async def test_missing_markoptions_logs_warning(caplog: pytest.LogCaptureFixture):
    """If MarkText is missing in options, a warning is logged and placeholder is used."""
    with caplog.at_level(logging.WARNING, logger="Bakalari API"):
        marks = await _prepare_marks_instance()
    # Verify the warning about MarkOptions not found is present
    assert any(
        "MarkOptions not found for MarkText" in rec.message for rec in caplog.records
    )


async def test_unknown_subject_logs_warning(caplog: pytest.LogCaptureFixture):
    """If a mark references a non-existent subject_id, a warning is logged and the mark is skipped."""
    payload = {
        "MarkOptions": [
            {"Id": "1", "Abbrev": "1", "Name": "Jedna"},
        ],
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
                        "SubjectId": "999",  # non-existent subject
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
        marks = await _prepare_marks_instance(payload=payload)

    # Warning is logged for unknown subject
    assert any(
        "Subject 999 not found for mark mx" in rec.message for rec in caplog.records
    )

    # Subject 101 exists, but the orphan mark (mx) must not be attached anywhere
    subjects = await marks.get_subjects()
    assert isinstance(subjects, list)
    assert len(subjects) == 1

    mat_marks = await marks.get_marks_by_subject("101")
    assert isinstance(mat_marks, list)
    assert len(mat_marks) == 0

    # Grouped result should be empty because no subject has any marks
    groups = await marks.get_marks_all()
    assert isinstance(groups, list)
    assert len(groups) == 0


async def test_combined_valid_and_orphan_marks(caplog: pytest.LogCaptureFixture):
    """Payload with both valid and orphan marks: only valid marks are kept, orphan logs warning."""
    payload = {
        "MarkOptions": [
            {"Id": "1", "Abbrev": "1", "Name": "Jedna"},
        ],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.0",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "mv",
                        "MarkDate": "2024-02-01T08:00:00+00:00",
                        "Caption": "Valid mark",
                        "Theme": "",
                        "MarkText": "1",
                        "Teacher": "Učitel X",
                        "SubjectId": "101",  # valid subject
                        "IsNew": False,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    },
                    {
                        "Id": "mo",
                        "MarkDate": "2024-02-02T08:00:00+00:00",
                        "Caption": "Orphan mark",
                        "Theme": "",
                        "MarkText": "1",
                        "Teacher": "Učitel X",
                        "SubjectId": "999",  # non-existent subject
                        "IsNew": False,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                    },
                ],
            }
        ],
    }

    with caplog.at_level(logging.WARNING, logger="Bakalari API"):
        marks = await _prepare_marks_instance(payload=payload)

    # Warning about orphan mark is logged
    assert any(
        "Subject 999 not found for mark mo" in rec.message for rec in caplog.records
    )

    # Subject exists
    subjects = await marks.get_subjects()
    assert isinstance(subjects, list)
    assert len(subjects) == 1
    assert subjects[0].id == "101"

    # Only valid mark 'mv' is present for subject 101
    mat_marks = await marks.get_marks_by_subject("101")
    assert isinstance(mat_marks, list)
    assert len(mat_marks) == 1
    assert mat_marks[0].id == "mv"

    # Grouped output includes only the valid mark
    groups = await marks.get_marks_all()
    assert isinstance(groups, list)
    assert len(groups) == 1
    assert groups[0].id == "101"
    mm = list(groups[0].marks)
    assert len(mm) == 1 and mm[0].id == "mv"


async def test_marks_marksoptions():
    """Marks.marksoptions returns a string representation of the options."""

    marks = await _prepare_marks_instance()

    assert "id: A abbrev: A text: Áčko" in marks.marksoptions.__str__()
    assert "id: 1 abbrev: 1 text: Jedna" in marks.marksoptions.__str__()
    assert "id: A abbrev: A text: Áčko" in marks.marksoptions.__format__("")

    assert "id: A abbrev: A text: Áčko" in marks.marksoptions.__format__("")


async def test_marks_markoptionsregistry():
    """Marks.marksoptionsregistry returns a string representation of the options."""

    marks = await _prepare_marks_instance()

    assert (
        marks.marksoptions.registry.__repr__()
        == "<MarkOptionsRegistry (id='1', abbr='1', text='Jedna'), (id='A', abbr='A', text='Áčko')>"
    )


async def test_marks_registry():
    """Test date functions"""

    marks = await _prepare_marks_instance()

    mat_marks = marks.subjects.get_marks("101")

    assert mat_marks.get_marks_by_date(date=None) == []
    assert (
        "id='m2'"
        in mat_marks.get_marks_by_date(
            date=dt.datetime(2024, 1, 5), subject_id="101"
        ).__repr__()
    )

    assert "<MarksRegistry" in repr(mat_marks)

    assert "MarksBase" in repr(mat_marks.get("m2"))
    assert "Písemka 2" in repr(mat_marks.get("m2"))
    assert "subject_id='101'" in repr(mat_marks.get("m2"))


async def test_format_points():
    """Marks.format_points returns a string representation of the points."""

    payload = {
        "MarkOptions": [
            {"Id": "1", "Abbrev": "1", "Name": "Jedna"},
        ],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.0",
                "PointsOnly": True,
                "Marks": [
                    {
                        "Id": "pt1",
                        "MarkDate": "2024-01-10T08:00:00+00:00",
                        "Caption": "Points 1",
                        "Theme": "",
                        "MarkText": "",
                        "Teacher": "Učitel",
                        "SubjectId": "101",
                        "IsNew": False,
                        "IsPoints": True,
                        "PointsText": 10,
                        "MaxPoints": None,
                    },
                    {
                        "Id": "pt2",
                        "MarkDate": "2024-01-15T08:00:00+00:00",
                        "Caption": "Points 2",
                        "Theme": "",
                        "MarkText": "",
                        "Teacher": "Učitel",
                        "SubjectId": "101",
                        "IsNew": False,
                        "IsPoints": True,
                        "PointsText": 20,
                        "MaxPoints": 100,
                    },
                ],
            }
        ],
    }

    marks = await _prepare_marks_instance(payload=payload)

    formatted = await marks.format_all_marks()

    # headers and some content present
    assert "Matematika (MAT) | average: 1.0" in formatted
    assert "points_only: True" in formatted
    assert "[2024-01-10] Points 1" in formatted
    assert "[2024-01-15] Points 2" in formatted
    assert "points: 10" in formatted
    assert "points: 20 / 100" in formatted
