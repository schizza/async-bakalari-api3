"""Tests for timetable parsing, formatting, context params, and fetch methods."""

from __future__ import annotations

from datetime import date, datetime

from async_bakalari_api.const import EndPoint
from async_bakalari_api.timetable import (
    Atom,
    Timetable,
    TimetableContext,
)
import pytest


def build_sample_payload() -> dict:
    """Return a representative timetable payload."""
    return {
        "Hours": [
            {"Id": 1, "Caption": "1", "BeginTime": "08:00", "EndTime": "08:45"},
        ],
        "Classes": [
            {"Id": "C1", "Abbrev": "1A", "Name": "Prvni A"},
        ],
        "Groups": [
            {"Id": "G1", "ClassId": "C1", "Abbrev": "G1", "Name": "Group 1"},
        ],
        "Subjects": [
            {"Id": "S1", "Abbrev": "MAT", "Name": "Matematika"},
        ],
        "Teachers": [
            {"Id": "T1", "Abbrev": "TR", "Name": "T. Ucitel"},
        ],
        "Rooms": [
            {"Id": "R1", "Abbrev": "R1", "Name": "Ucebna 1"},
        ],
        "Cycles": [
            {"Id": "CY1", "Abbrev": "C1", "Name": "Cycle 1"},
        ],
        "Days": [
            # Intentionally first a later date, to verify sort in format_week
            {
                "DayOfWeek": 1,
                "Date": "2024-04-08T00:00:00",
                "DayDescription": "Popis",
                "DayType": "Workday",
                "Atoms": [
                    {
                        "HourId": 1,
                        "GroupIds": ["G1"],
                        "SubjectId": "S1",
                        "TeacherId": "T1",
                        "RoomId": "R1",
                        "CycleIds": [],
                        "HomeworkIds": ["H1", "H2"],
                        "Theme": "Zlomky",
                        "Change": {
                            "ChangeSubject": "MAT",
                            "Day": "2024-04-08",
                            "Hours": "1",
                            "ChangeType": "Změna",
                            "Description": "Upraveno",
                            "Time": "09:00",
                            "TypeAbbrev": "CH",
                            "TypeName": "Change",
                        },
                    }
                ],
            },
            # Earlier date with no atoms -> should print empty placeholder
            {
                "DayOfWeek": 7,
                "Date": "2024-04-07",
                "DayDescription": "",
                "DayType": "Weekend",
                "Atoms": [],
            },
        ],
    }


class DummyBakalari:
    """A minimal stub of Bakalari to capture requests."""

    def __init__(self, payload: dict | None = None):
        """Initialize the DummyBakalari instance."""

        self.calls: list[tuple[EndPoint, dict | None]] = []
        self.payload = payload if payload is not None else {}

    async def send_auth_request(self, request_endpoint: EndPoint, **kwargs):
        """Send an authentication request."""
        # store only what we assert in tests (endpoint + params)
        self.calls.append((request_endpoint, kwargs.get("params")))
        return self.payload

    # Timetable.__aenter__/__aexit__ call these; keep as no-ops if needed
    async def _ensure_session(self):
        return None

    async def __aexit__(self, *_):
        """Exit the context manager."""
        return None


def test_timetable_context_to_params_mapping():
    """Test mapping of TimetableContext to parameters."""
    assert TimetableContext("class", "C1").to_params() == {"classId": "C1"}
    assert TimetableContext("group", "G1").to_params() == {"groupId": "G1"}
    assert TimetableContext("teacher", "T1").to_params() == {"teacherId": "T1"}
    assert TimetableContext("room", "R1").to_params() == {"roomId": "R1"}
    assert TimetableContext("student", "S1").to_params() == {"studentId": "S1"}


def test_parse_timetable_and_resolve_and_formatting():
    """Test parsing timetable and resolving entities."""

    payload = build_sample_payload()

    # Use real Timetable parser by injecting stub Bakalari that returns our payload
    dummy = DummyBakalari(payload)
    tt = Timetable(dummy)  # pyright: ignore[]

    # Private method call is fine in tests
    week = tt._parse_timetable(payload)  # noqa: SLF001

    # Parsed hours
    assert 1 in week.hours
    assert week.hours[1].caption == "1"
    assert week.hours[1].begin_time == "08:00"
    assert week.hours[1].end_time == "08:45"

    # Entities
    assert week.subjects["S1"].abbrev == "MAT"
    assert week.teachers["T1"].abbrev == "TR"
    assert week.rooms["R1"].abbrev == "R1"
    assert week.groups["G1"].class_id == "C1"

    # Days
    assert len(week.days) == 2
    day1 = week.get_day_by_weekday(1)
    assert day1 is not None
    assert day1.description == "Popis"
    assert day1.day_type == "Workday"
    assert len(day1.atoms) == 1

    # Resolve atom relations
    atom = day1.atoms[0]
    subj, teach, room, groups = week.resolve(atom)
    assert subj and subj.abbrev == "MAT"
    assert teach and teach.abbrev == "TR"
    assert room and room.abbrev == "R1"
    assert groups and groups[0].abbrev == "G1"

    # Formatting a day with atoms
    s = week.format_day(day1)
    lines = s.splitlines()
    expected_header = f"{day1.date.date()} ({day1.day_type}) - {day1.description}"
    assert lines[0] == expected_header
    assert lines[1] == "-" * len(expected_header)
    # "  " + f"{hour_label:>2}", where hour_label is "1" -> results in "   1 ..."
    assert lines[2] == "   1 [08:00-08:45] MAT (G1) — TR @ R1"
    assert lines[3] == "     předmět: Zlomky"
    assert lines[4] == "     změna: Změna | Upraveno (09:00)"

    # Formatting of empty day
    day2 = week.get_day_by_weekday(7)
    assert day2 is not None
    s2 = week.format_day(day2)
    lines2 = s2.splitlines()
    expected_header2 = f"{day2.date.date()} ({day2.day_type})"
    assert lines2[0] == expected_header2
    assert lines2[1] == "-" * len(expected_header2)
    assert lines2[2] == "  [Žádný záznam]"

    # Formatting of week should be in chronological order and not end with a trailing newline
    wfmt = week.format_week()
    assert not wfmt.endswith("\n")
    assert wfmt.splitlines()[0].startswith("2024-04-07 (")

    # get_day_by_date accepts both datetime and date
    by_date = week.get_day_by_date(date(2024, 4, 8))
    by_dt = week.get_day_by_date(datetime(2024, 4, 8, 12, 34))
    none_rt = week.get_day_by_date(datetime(2023, 4, 8, 12, 34, 59))
    none_wd = week.get_day_by_weekday(8)
    assert by_date is day1 and by_dt is day1
    assert none_rt is None
    assert none_wd is None

    # Resolve with missing entities should return Nones/empty
    lonely_atom = Atom(
        hour_id=99,
        group_ids=["NOPE"],
        subject_id="X",
        teacher_id="Y",
        room_id="Z",
        cycle_ids=[],
        change=None,
        homework_ids=[],
        theme=None,
    )
    subj2, teach2, room2, groups2 = week.resolve(lonely_atom)
    assert subj2 is None and teach2 is None and room2 is None and groups2 == []


@pytest.mark.asyncio
async def test_fetch_actual_builds_params_and_sets_last():
    """Test fetching actual timetable with various parameters."""
    dummy = DummyBakalari(payload={})  # empty payload is OK for parser
    tt = Timetable(dummy)  # pyright: ignore[]

    # Explicit date + TimetableContext
    d = date(2023, 1, 2)
    ctx = TimetableContext("class", "C1")
    week = await tt.fetch_actual(for_date=d, context=ctx)
    assert isinstance(week.days, list)  # parsed structure returned
    assert len(dummy.calls) == 1
    ep, params = dummy.calls[-1]
    assert ep is EndPoint.TIMETABLE_ACTUAL
    assert params["date"] == "2023-01-02" and params["classId"] == "C1"  # pyright: ignore[]
    assert tt.get_last_actual() is week

    # Datetime date + dict context
    d2 = datetime(2024, 1, 6, 12, 0)
    week2 = await tt.fetch_actual(for_date=d2, context={"teacherId": "T9"})
    assert tt.get_last_actual() is week2
    ep2, params2 = dummy.calls[-1]
    assert ep2 is EndPoint.TIMETABLE_ACTUAL
    assert params2["date"] == "2024-01-06" and params2["teacherId"] == "T9"  # pyright: ignore[]

    # None date -> today
    week3 = await tt.fetch_actual()
    assert tt.get_last_actual() is week3
    ep3, params3 = dummy.calls[-1]
    assert ep3 is EndPoint.TIMETABLE_ACTUAL
    assert "date" in params3 and params3["date"] == datetime.now().date().strftime(  # pyright: ignore[]
        "%Y-%m-%d"
    )


@pytest.mark.asyncio
async def test_fetch_permanent_builds_params_and_sets_last():
    """Test fetching permanent timetable and setting last permanent."""

    dummy = DummyBakalari(payload={})
    tt = Timetable(dummy)  # pyright: ignore[]

    # No context -> params None
    week = await tt.fetch_permanent()
    assert tt.get_last_permanent() is week
    ep, params = dummy.calls[-1]
    assert ep is EndPoint.TIMETABLE_PERMANENT
    assert params is None

    # With TimetableContext
    ctx = TimetableContext("room", "R99")
    week2 = await tt.fetch_permanent(context=ctx)
    assert tt.get_last_permanent() is week2
    ep2, params2 = dummy.calls[-1]
    assert ep2 is EndPoint.TIMETABLE_PERMANENT
    assert params2 == {"roomId": "R99"}

    # With dict context
    await tt.fetch_permanent(context={"studentId": "S777"})
    ep3, params3 = dummy.calls[-1]
    assert ep3 is EndPoint.TIMETABLE_PERMANENT
    assert params3 == {"studentId": "S777"}


@pytest.mark.asyncio
async def test_timetable_async_context_manager_calls_bakalari():
    """Test TimetableContextManager calls bakalari."""

    called = {"ensure": 0, "exit": 0}

    class CtxBakalari(DummyBakalari):
        async def _ensure_session(self):
            called["ensure"] += 1

        async def __aexit__(self, *args):
            called["exit"] += 1

    async with Timetable(CtxBakalari(payload={})) as t:  # pyright: ignore[]
        assert isinstance(t, Timetable)

    assert called["ensure"] == 1
    assert called["exit"] == 1


def test_parser_handles_invalid_entries_and_change_and_day_skip():
    """Test parser handles invalid entries and change and day skip."""

    # Craft payload to trigger exception branches in parser:
    # - Invalid types in entity lists (no .get -> AttributeError)
    # - Invalid hour Id (int conversion fails)
    # - Change with invalid Day (dateutil.parse raises)
    # - One invalid day entry (non-dict) to trigger skip
    data = {
        "Hours": [{"Id": "X"}],  # invalid int conversion
        "Classes": [123],  # invalid element (no .get)
        "Groups": [123],
        "Subjects": [123],
        "Teachers": [123],
        "Rooms": [123],
        "Cycles": [123],
        "Days": [
            42,  # invalid day entry, triggers skip
            {
                "DayOfWeek": 1,
                "Date": "2024-05-01",
                "DayDescription": "",
                "DayType": "Workday",
                "Atoms": [
                    {
                        "HourId": 1,
                        "GroupIds": [],
                        "SubjectId": None,
                        "TeacherId": None,
                        "RoomId": None,
                        "CycleIds": [],
                        "HomeworkIds": [],
                        "Theme": None,
                        "Change": {
                            "Day": "not a date"
                        },  # invalid, triggers change except
                    }
                ],
            },
        ],
    }

    tt = Timetable(DummyBakalari({}))  # pyright: ignore[]
    week = tt._parse_timetable(data)  # noqa: SLF001

    # Hours/Entities with invalid entries are skipped, valid day still parsed
    assert week.hours == {}
    assert week.classes == {}
    assert week.groups == {}
    assert week.subjects == {}
    assert week.teachers == {}
    assert week.rooms == {}
    assert week.cycles == {}

    # One valid day remains (the non-dict day is skipped)
    assert len(week.days) == 1
    d = week.days[0]
    assert d.day_of_week == 1
    assert len(d.atoms) == 1
    # Change payload was invalid -> change is None
    assert d.atoms[0].change is None
