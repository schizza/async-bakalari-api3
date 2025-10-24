"""Module for working with Timetable (rozvrh) using Bakalari API v3."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date as date_cls
from typing import Any, Dict, List, Optional, Tuple, Literal

from dateutil import parser as dt_parser

from .bakalari import Bakalari
from .const import EndPoint
from .logger_api import api_logger

log = api_logger("Bakalari API").get()


# ---- Data structures ----
@dataclass(frozen=True)
class Hour:
    """Represents one timetable hour slot definition."""

    id: int
    caption: str
    begin_time: str
    end_time: str


@dataclass(frozen=True)
class Change:
    """Represents a change to an atom."""

    change_subject: Optional[str]
    day: datetime
    hours: Optional[str]
    change_type: Optional[str]
    description: Optional[str]
    time: Optional[str]
    type_abbrev: Optional[str]
    type_name: Optional[str]


@dataclass(frozen=True)
class Atom:
    """Represents one timetable atom (lesson block or change placeholder)."""

    hour_id: int
    group_ids: List[str]
    subject_id: Optional[str]
    teacher_id: Optional[str]
    room_id: Optional[str]
    cycle_ids: List[str]
    change: Optional[Change]
    homework_ids: List[str]
    theme: Optional[str]


@dataclass(frozen=True)
class DayEntry:
    """Represents a single day in the timetable."""

    day_of_week: int
    date: datetime
    description: str
    day_type: str
    atoms: List[Atom]


@dataclass(frozen=True)
class ClassEntity:
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class GroupEntity:
    class_id: Optional[str]
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class SubjectEntity:
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class TeacherEntity:
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class RoomEntity:
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class CycleEntity:
    id: str
    abbrev: str
    name: str


@dataclass(frozen=True)
class TimetableContext:
    """Context for timetable filtering (class, group, teacher, room, student)."""

    kind: Literal["class", "group", "teacher", "room", "student"]
    id: str

    def to_params(self) -> Dict[str, str]:
        """Return query parameters for the selected context."""
        key = {
            "class": "classId",
            "group": "groupId",
            "teacher": "teacherId",
            "room": "roomId",
            "student": "studentId",
        }[self.kind]
        return {key: self.id}


@dataclass
class TimetableWeek:
    """Parsed timetable container for a week (actual or permanent)."""

    hours: Dict[int, Hour] = field(default_factory=dict)
    days: List[DayEntry] = field(default_factory=list)
    classes: Dict[str, ClassEntity] = field(default_factory=dict)
    groups: Dict[str, GroupEntity] = field(default_factory=dict)
    subjects: Dict[str, SubjectEntity] = field(default_factory=dict)
    teachers: Dict[str, TeacherEntity] = field(default_factory=dict)
    rooms: Dict[str, RoomEntity] = field(default_factory=dict)
    cycles: Dict[str, CycleEntity] = field(default_factory=dict)

    def get_day_by_date(self, day: datetime | date_cls) -> Optional[DayEntry]:
        """Return the DayEntry for the given date (date part only)."""

        target = day.date() if isinstance(day, datetime) else day
        for d in self.days:
            if d.date.date() == target:
                return d
        return None

    def get_day_by_weekday(self, weekday: int) -> Optional[DayEntry]:
        """Return the DayEntry by weekday index from API (1=Mon ... 7=Sun if present)."""
        for d in self.days:
            if d.day_of_week == weekday:
                return d
        return None

    def resolve(self, atom: Atom) -> Tuple[Optional[SubjectEntity], Optional[TeacherEntity], Optional[RoomEntity], List[GroupEntity]]:
        """Resolve atom relations to entities by their IDs."""
        subj = self.subjects.get(atom.subject_id.strip()) if atom.subject_id else None
        teach = self.teachers.get(atom.teacher_id.strip()) if atom.teacher_id else None
        room = self.rooms.get(atom.room_id.strip()) if atom.room_id else None
        groups = []
        for gid in atom.group_ids or []:
            g = self.groups.get(gid.strip())
            if g:
                groups.append(g)
        return subj, teach, room, groups

    def format_day(self, day: DayEntry) -> str:
        """Return a formatted string of the day's timetable."""
        lines: List[str] = []
        header = f"{day.date.date()} ({day.day_type})"
        if day.description:
            header += f" - {day.description}"
        lines.append(header)
        lines.append("-" * len(header))
        if not day.atoms:
            lines.append("  [Žádný záznam]")
            return "\n".join(lines)

        for atom in day.atoms:
            hour = self.hours.get(atom.hour_id)
            subj, teach, room, groups = self.resolve(atom)

            hour_label = f"{hour.caption if hour else atom.hour_id}"
            time_span = f"{hour.begin_time}-{hour.end_time}" if hour else ""
            subj_label = subj.abbrev if subj else ""
            teach_label = teach.abbrev if teach else ""
            room_label = room.abbrev if room else ""
            groups_label = ",".join(g.abbrev for g in groups) if groups else ""

            # Base line
            base = f"  {hour_label:>2} [{time_span}] {subj_label}"
            if groups_label:
                base += f" ({groups_label})"
            if teach_label:
                base += f" — {teach_label}"
            if room_label:
                base += f" @ {room_label}"
            lines.append(base)

            # Theme
            if atom.theme:
                lines.append(f"     předmět: {atom.theme}")

            # Change
            if atom.change:
                ch = atom.change
                ch_label = f"     změna: {ch.change_type or ''} | {ch.description or ''}"
                if ch.time:
                    ch_label += f" ({ch.time})"
                lines.append(ch_label)

        return "\n".join(lines)

    def format_week(self) -> str:
        """Return formatted string of the entire week."""
        parts: List[str] = []
        for d in sorted(self.days, key=lambda x: x.date):
            parts.append(self.format_day(d))
            parts.append("")  # blank line
        return "\n".join(parts).rstrip()


class Timetable:
    """Client for fetching and parsing timetable endpoints."""

    def __init__(self, bakalari: Bakalari) -> None:
        """Initialize Timetable client."""
        self.bakalari = bakalari
        self._last_actual: Optional[TimetableWeek] = None
        self._last_permanent: Optional[TimetableWeek] = None

    async def __aenter__(self) -> "Timetable":
        """Support usage as an async context manager: `async with Timetable(b) as t:`"""
        await self.bakalari.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Close underlying Bakalari session on context exit."""
        await self.bakalari.__aexit__(exc_type, exc, tb)

    # Public API
    async def fetch_actual(self, for_date: Optional[datetime | date_cls] = None, context: Optional["TimetableContext | Dict[str, str]"] = None) -> TimetableWeek:
        """Fetch actual timetable for a specific date (defaults to today).

        Args:
            for_date: date or datetime to fetch week for.
            context: timetable context (e.g., class/group/teacher/room/student).
                     You can pass TimetableContext or a dict of extra query params.
        """
        if for_date is None:
            for_date = datetime.now().date()
        if isinstance(for_date, datetime):
            dt_value = for_date.date()
        else:
            dt_value = for_date
        query_date = dt_value.strftime("%Y-%m-%d")

        params: Dict[str, Any] = {"date": query_date}
        if context is not None:
            if isinstance(context, TimetableContext):
                params.update(context.to_params())
            elif isinstance(context, dict):
                params.update(context)

        log.debug(f"Fetching actual timetable for date={query_date} context={context}")
        data = await self.bakalari.send_auth_request(
            EndPoint.TIMETABLE_ACTUAL,
            params=params,
        )
        week = self._parse_timetable(data)
        self._last_actual = week
        return week

    async def fetch_permanent(self, context: Optional["TimetableContext | Dict[str, str]"] = None) -> TimetableWeek:
        """Fetch permanent timetable.

        Args:
            context: timetable context; pass TimetableContext or dict of extra query params.
        """
        params: Optional[Dict[str, Any]] = None
        if context is not None:
            params = {}
            if isinstance(context, TimetableContext):
                params.update(context.to_params())
            elif isinstance(context, dict):
                params.update(context)

        log.debug(f"Fetching permanent timetable context={context}")
        data = await self.bakalari.send_auth_request(
            EndPoint.TIMETABLE_PERMANENT,
            params=params,
        )
        week = self._parse_timetable(data)
        self._last_permanent = week
        return week

    def get_last_actual(self) -> Optional[TimetableWeek]:
        """Return last fetched actual timetable week, if any."""
        return self._last_actual

    def get_last_permanent(self) -> Optional[TimetableWeek]:
        """Return last fetched permanent timetable week, if any."""
        return self._last_permanent

    # Parsing
    def _parse_timetable(self, data: Dict[str, Any]) -> TimetableWeek:
        """Parse timetable JSON payload into structured TimetableWeek."""
        week = TimetableWeek()

        # Hours
        for h in data.get("Hours", []) or []:
            try:
                hour = Hour(
                    id=int(h.get("Id")),
                    caption=str(h.get("Caption", "")),
                    begin_time=str(h.get("BeginTime", "")),
                    end_time=str(h.get("EndTime", "")),
                )
                week.hours[hour.id] = hour
            except Exception as ex:
                log.warning(f"Skipping invalid hour entry {h!r}: {ex}")

        # Entities
        for c in data.get("Classes", []) or []:
            try:
                week.classes[str(c.get("Id")).strip()] = ClassEntity(
                    id=str(c.get("Id")).strip(),
                    abbrev=str(c.get("Abbrev", "")),
                    name=str(c.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid class entry {c!r}: {ex}")

        for g in data.get("Groups", []) or []:
            try:
                week.groups[str(g.get("Id")).strip()] = GroupEntity(
                    class_id=(str(g.get("ClassId")).strip() if g.get("ClassId") is not None else None),
                    id=str(g.get("Id")).strip(),
                    abbrev=str(g.get("Abbrev", "")),
                    name=str(g.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid group entry {g!r}: {ex}")

        for s in data.get("Subjects", []) or []:
            try:
                week.subjects[str(s.get("Id")).strip()] = SubjectEntity(
                    id=str(s.get("Id")).strip(),
                    abbrev=str(s.get("Abbrev", "")),
                    name=str(s.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid subject entry {s!r}: {ex}")

        for t in data.get("Teachers", []) or []:
            try:
                week.teachers[str(t.get("Id")).strip()] = TeacherEntity(
                    id=str(t.get("Id")).strip(),
                    abbrev=str(t.get("Abbrev", "")),
                    name=str(t.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid teacher entry {t!r}: {ex}")

        for r in data.get("Rooms", []) or []:
            try:
                week.rooms[str(r.get("Id")).strip()] = RoomEntity(
                    id=str(r.get("Id")).strip(),
                    abbrev=str(r.get("Abbrev", "")),
                    name=str(r.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid room entry {r!r}: {ex}")

        for cy in data.get("Cycles", []) or []:
            try:
                week.cycles[str(cy.get("Id")).strip()] = CycleEntity(
                    id=str(cy.get("Id")).strip(),
                    abbrev=str(cy.get("Abbrev", "")),
                    name=str(cy.get("Name", "")),
                )
            except Exception as ex:
                log.warning(f"Skipping invalid cycle entry {cy!r}: {ex}")

        # Days + Atoms
        for d in data.get("Days", []) or []:
            try:
                day_atoms: List[Atom] = []
                for a in d.get("Atoms", []) or []:
                    change_obj = None
                    raw_change = a.get("Change")
                    if raw_change:
                        try:
                            change_obj = Change(
                                change_subject=raw_change.get("ChangeSubject"),
                                day=dt_parser.parse(raw_change.get("Day"))
                                if raw_change.get("Day")
                                else dt_parser.parse(d.get("Date"))
                                if d.get("Date")
                                else datetime.now(),
                                hours=raw_change.get("Hours"),
                                change_type=raw_change.get("ChangeType"),
                                description=raw_change.get("Description"),
                                time=raw_change.get("Time"),
                                type_abbrev=raw_change.get("TypeAbbrev"),
                                type_name=raw_change.get("TypeName"),
                            )
                        except Exception as ex:
                            log.warning(f"Invalid change payload {raw_change!r}: {ex}")

                    atom = Atom(
                        hour_id=int(a.get("HourId")),
                        group_ids=[str(g) for g in (a.get("GroupIds") or [])],
                        subject_id=(str(a.get("SubjectId")) if a.get("SubjectId") is not None else None),
                        teacher_id=(str(a.get("TeacherId")) if a.get("TeacherId") is not None else None),
                        room_id=(str(a.get("RoomId")) if a.get("RoomId") is not None else None),
                        cycle_ids=[str(c) for c in (a.get("CycleIds") or [])],
                        change=change_obj,
                        homework_ids=[str(h) for h in (a.get("HomeworkIds") or [])],
                        theme=a.get("Theme"),
                    )
                    day_atoms.append(atom)

                day_entry = DayEntry(
                    day_of_week=int(d.get("DayOfWeek")),
                    date=dt_parser.parse(d.get("Date")) if d.get("Date") else datetime.now(),
                    description=str(d.get("DayDescription", "")),
                    day_type=str(d.get("DayType", "")),
                    atoms=day_atoms,
                )
                week.days.append(day_entry)
            except Exception as ex:
                log.warning(f"Skipping invalid day entry {d!r}: {ex}")

        return week
