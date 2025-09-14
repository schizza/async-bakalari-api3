"""Module to handle marks from Bakalari."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, overload

from dateutil import parser

from .bakalari import Bakalari
from .const import EndPoint
from .logger_api import api_logger

log = api_logger("Bakalari API").get()


@dataclass
class MarkOptionsBase:
    """Mark options base."""

    id: str
    abbr: str
    text: str


class MarkOptionsRegistry:
    """Mark options registry."""

    def __init__(self):
        """Initialize MarkOptionsRegistry."""

        self._data: dict[str, MarkOptionsBase] = {}
        self._index: set = set()

    def append(self, marksoptions: MarkOptionsBase):
        """Set mark options."""
        if marksoptions.id not in self._index:
            self._data[marksoptions.id] = marksoptions
            self._index.add(marksoptions.id)

    def get(self, id: str) -> MarkOptionsBase | None:
        """Get mark options."""
        return self._data.get(id, None)

    def __repr__(self) -> str:
        """Representation of MarkOptionsRegistry."""

        items = ", ".join(
            f"(id={mo.id!r}, abbr={mo.abbr!r}, text={mo.text!r})"
            for mo in self._data.values()
        )
        return f"<MarkOptionsRegistry {items}>"

    def __str__(self) -> str:
        """Return string representation of data."""
        return "\n".join(
            f"id: {idx} abbrev: {self._data[idx].abbr} text: {self._data[idx].text}"
            for idx in self._index
        )


class MarkOptions(MarkOptionsRegistry):
    """Mark options."""

    def __init__(self):
        """Initialize MarkOptions."""
        self.registry = MarkOptionsRegistry()

    def append(self, marksoptions: MarkOptionsBase):
        """Append mark options."""
        self.registry.append(marksoptions=marksoptions)

    def __str__(self) -> str:
        """Return string representation of data."""
        return f"{self.registry}"

    def __getitem__(self, key: str) -> MarkOptionsBase | None:
        """Get mark options."""
        return self.registry.get(key)

    def __format__(self, format_spec: str) -> str:
        """Format string representation of data."""
        return self.__str__()


@dataclass
class MarksBase:
    """Marks base."""

    id: str
    date: datetime
    caption: str
    theme: str | None
    marktext: MarkOptionsBase | None
    teacher: str | None
    subject_id: str
    is_new: bool
    is_points: bool
    points_text: str | None
    max_points: int | None

    def __str__(self) -> str:
        """Return string representation of data."""

        return (
            f"theme: {(self.theme or '').rstrip('\n')}: {' ' * 5}{(self.marktext.text if self.marktext else '')}\n"
            f"date: {self.date.date()}\n"
            f"id: {self.id}\n"
            f"is_new: {self.is_new}\n"
            f"is_points: {self.is_points}\n"
            f"points_text: {self.points_text}\n"
            f"max_points: {self.max_points}\n\n"
        )


class MarksRegistry:
    """Marks registry."""

    def __init__(self):
        """Initialize MarksRegistry."""

        self._data: dict[str, MarksBase] = {}
        self._index: set = set()

    def append(self, marks: MarksBase):
        """Set marks."""
        if marks.id not in self._index:
            self._data[marks.id] = marks
            self._index.add(marks.id)

    def find_new_marks(self) -> list[MarksBase]:
        """Find new marks."""

        return [mark for mark in self._data.values() if mark.is_new]

    @overload
    def get_marks_by_date(
        self, date: datetime, date_to: datetime
    ) -> list[MarksBase]: ...
    @overload
    def get_marks_by_date(self, date: datetime) -> list[MarksBase]: ...
    @overload
    def get_marks_by_date(
        self, subject_id: str, date: datetime, date_to: datetime
    ) -> list[MarksBase]: ...
    @overload
    def get_marks_by_date(self, subject_id: str, date: datetime) -> list[MarksBase]: ...

    def get_marks_by_date(
        self,
        subject_id: str | None = None,
        date: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[MarksBase]:
        """Get marks by date or date range. Or for subject by date or date range."""
        if date is None:
            return []

        start = date.date()
        end = date_to.date() if date_to is not None else start

        if subject_id is not None:
            return [
                mark
                for mark in self._data.values()
                if mark.subject_id == subject_id and start <= mark.date.date() <= end
            ]

        return [
            mark for mark in self._data.values() if start <= mark.date.date() <= end
        ]

    def get(self, id: str) -> MarksBase | None:
        """Get marks."""
        return self._data.get(id, None)

    def __repr__(self) -> str:
            """Representation of MarksRegistry."""
            items = ", ".join(
                f"(id={data.id!r}, date={data.date!r}, caption={data.caption!r}, theme={data.theme!r}, marktext={data.marktext!r}, teacher={data.teacher!r}, subject_id={data.subject_id!r}, is_new={data.is_new!r}, is_points={data.is_points!r}, points_text={data.points_text!r}, max_points={data.max_points!r})"
                for data in self._data.values()
            )
            return f"<MarksRegistry {items}>"

    def __iter__(self):
        """Iterate over marks."""
        yield from self._data.values()

    def __str__(self) -> str:
        """Return string representation of data."""
        return "\n".join(
            f"id: {idx} date: {self._data[idx].date} caption: {self._data[idx].caption} theme: {self._data[idx].theme} marktext: {self._data[idx].marktext} teacher: {self._data[idx].teacher} subject_id: {self._data[idx].subject_id} is_new: {self._data[idx].is_new} is_points: {self._data[idx].is_points} points_text: {self._data[idx].points_text} max_points: {self._data[idx].max_points}"
            for idx in self._index
        )


class SubjectsBase:
    """Subjects base."""

    id: str
    abbr: str
    name: str
    average_text: str
    points_only: bool
    marks: MarksRegistry

    def __init__(
        self, *, id: str, abbr: str, name: str, average_text: str, points_only: bool
    ) -> None:
        """Initialize SubjectsBase."""
        self.marks = MarksRegistry()
        self._data: dict[str, Any] = {}

        _setter = object.__setattr__
        _setter(self, "id", id)
        _setter(self, "abbr", abbr)
        _setter(self, "average_text", average_text)
        _setter(self, "points_only", points_only)
        _setter(self, "name", name)

    def __repr__(self) -> str:
        """Representation of SubjectsBase."""
        return f"<SubjectsBase id={self.id} abbr={self.abbr} name={self.name}>"

    def __str__(self) -> str:
        """Return string representation of data."""
        return (
            f"name: {self.name}\n"
            f"id: {self.id}\n"
            f"abbr: {self.abbr}\n"
            f"Average: {self.average_text}\n"
            f"points_only: {self.points_only}\n"
            f"----\n"
        )


class SubjectsRegistry:
    """Subjects registry."""

    def __init__(self):
        """Initialize SubjectsRegistry."""

        self._subjects: dict[str, SubjectsBase] = {}
        self._index: set = set()

    def append_subject(self, subjects: SubjectsBase):
        """Set subjects."""
        if subjects.id not in self._index:
            self._subjects[subjects.id] = subjects
            self._index.add(subjects.id)

    def append_marks(self, marks: MarksBase):
        """Set marks."""
        subject = self._subjects.get(marks.subject_id)
        if subject:
            subject.marks.append(marks)
        else:
            log.warning(f"Subject {marks.subject_id} not found for mark {marks.id}")

    def get_subject(self, id: str) -> SubjectsBase | None:
        """Get subjects."""
        return self._subjects.get(id, None)

    def get_marks(self, subject_id: str) -> MarksRegistry:
        """Get marks for subject"""

        return self._subjects[subject_id].marks

    def __repr__(self) -> str:
        """Representation of SubjectsRegistry."""
        items = ", ".join(
            f"(id={s.id!r}, abbr={s.abbr!r}, name={s.name!r})"
            for s in self._subjects.values()
        )
        return f"<SubjectsRegistry {items}>"

    def __str__(self) -> str:
        """Return string representation of data."""
        return "\n".join(
            f"id: {idx} abbr: {self._subjects[idx].abbr} name: {self._subjects[idx].name} average_text: {self._subjects[idx].average_text} points_only: {self._subjects[idx].points_only}"
            for idx in self._index
        )


class Marks:
    """Marks class."""

    def __init__(self, bakalari: Bakalari):
        """Initialize Marks."""
        self.bakalari = bakalari
        self.marksoptions = MarkOptions()
        self.subjects = SubjectsRegistry()

    async def _parse_marks_options(self, options: list[dict[str, str]]):
        """Parse mark options."""
        for option in options:
            self.marksoptions.append(
                marksoptions=MarkOptionsBase(
                    id=option.get("Id"),
                    abbr=option.get("Abbrev"),
                    text=option.get("Name"),
                )
            )

    async def _parse_subjects(self, subjects: dict[str, Any]):
        """Parse subjects."""

        self.subjects.append_subject(
            subjects=SubjectsBase(
                id=subjects["Subject"].get("Id"),
                abbr=subjects["Subject"].get("Abbrev"),
                name=subjects["Subject"].get("Name"),
                average_text=subjects.get("AverageText"),
                points_only=subjects.get("PointsOnly"),
            )
        )
        for mark in subjects["Marks"]:
            raw_mt_id = mark.get("MarkText")
            opt = self.marksoptions[raw_mt_id]
            if opt is None:
                log.warning(
                    f"MarkOptions not found for MarkText={raw_mt_id!r}; using placeholder"
                )
                opt = MarkOptionsBase(
                    id=raw_mt_id, abbr=raw_mt_id or "", text=raw_mt_id or ""
                )
            self.subjects.append_marks(
                marks=MarksBase(
                    id=mark.get("Id"),
                    date=parser.parse(mark.get("MarkDate")),
                    caption=mark.get("Caption"),
                    theme=mark.get("Theme"),
                    marktext=opt,
                    teacher=mark.get("Teacher"),
                    subject_id=mark.get("SubjectId"),
                    is_new=mark.get("IsNew"),
                    is_points=mark.get("IsPoints"),
                    points_text=mark.get("PointsText"),
                    max_points=mark.get("MaxPoints"),
                )
            )

    async def fetch_marks(self):
        """Fetch marks from Bakalari."""
        response = await self.bakalari.send_auth_request(EndPoint.MARKS)

        await self._parse_marks_options(response.get("MarkOptions"))

        tasks = [
            asyncio.create_task(self._parse_subjects(subjects))
            for subjects in response.get("Subjects")
        ]

        await asyncio.gather(*tasks)

    async def get_subjects(self) -> list[SubjectsBase]:
        """Get list subjects."""
        return list(self.subjects._subjects.values())

    async def get_marks_by_subject(self, subject_id: str) -> list[MarksBase]:
        """Get marks for subject."""
        subject = self.subjects.get_subject(subject_id)
        return list(subject.marks) if subject else []

    async def get_new_marks(self) -> list[SubjectsBase]:
        """Get new marks for subject."""

        new_marks: list[SubjectsBase] = []

        for subject in self.subjects._subjects.values():
            if len(found := subject.marks.find_new_marks()) != 0:
                new_marks.append(
                    SubjectsBase(
                        id=subject.id,
                        abbr=subject.abbr,
                        name=subject.name,
                        average_text=subject.average_text,
                        points_only=subject.points_only,
                    )
                )
                for mark in found:
                    new_marks[-1].marks.append(mark)
        return new_marks

    async def get_marks_all(
        self,
        date: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> list[SubjectsBase]:
        """Get all marks grouped by subject. Optionally filter by date or date range and/or subject."""

        results: list[SubjectsBase] = []

        if subject_id is not None:
            subject = self.subjects.get_subject(subject_id)
            if not subject:
                return results

            if date is None:
                marks = list(subject.marks)
            else:
                marks = subject.marks.get_marks_by_date(date=date, date_to=date_to)

            if marks:
                container = SubjectsBase(
                    id=subject.id,
                    abbr=subject.abbr,
                    name=subject.name,
                    average_text=subject.average_text,
                    points_only=subject.points_only,
                )
                for mark in marks:
                    container.marks.append(mark)
                results.append(container)
            return results

        for subject in self.subjects._subjects.values():
            if date is None:
                marks = list(subject.marks)
            else:
                marks = subject.marks.get_marks_by_date(date=date, date_to=date_to)

            if marks:
                container = SubjectsBase(
                    id=subject.id,
                    abbr=subject.abbr,
                    name=subject.name,
                    average_text=subject.average_text,
                    points_only=subject.points_only,
                )
                for mark in marks:
                    container.marks.append(mark)
                results.append(container)

        return results

    async def format_all_marks(
        self,
        date: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> str:
        """Return a nicely formatted string of all marks, grouped by subject."""
        groups = await self.get_marks_all(
            date=date, date_to=date_to, subject_id=subject_id
        )
        lines: list[str] = []
        for subj in groups:
            header = f"{subj.name} ({subj.abbr}) | average: {subj.average_text} | points_only: {subj.points_only}"
            lines.append(header)
            lines.append("-" * len(header))
            for m in subj.marks:
                mark_text = m.marktext.text if m.marktext else ""
                caption = m.caption or ""
                line = f"  [{m.date.date()}] {caption} -> {mark_text}"
                if m.is_new:
                    line += " [NEW]"
                lines.append(line)
                if m.theme:
                    lines.append(f"    theme: {m.theme.strip()}")
                if m.is_points:
                    pt = m.points_text or ""
                    if m.max_points is not None:
                        lines.append(f"    points: {pt} / {m.max_points}")
                    else:
                        lines.append(f"    points: {pt}")
            lines.append("")  # blank line between subjects
        return "\n".join(lines).rstrip()


    async def get_new_marks_by_date(
        self,
        date: datetime,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> list[SubjectsBase]:
        """Get new marks by date or date range. Optionally for a specific subject."""

        new_marks: list[SubjectsBase] = []

        if subject_id is not None:
            subject = self.subjects.get_subject(subject_id)
            if not subject:
                return new_marks
            marks = [
                m
                for m in subject.marks.get_marks_by_date(date=date, date_to=date_to)
                if m.is_new
            ]
            if marks:
                container = SubjectsBase(
                    id=subject.id,
                    abbr=subject.abbr,
                    name=subject.name,
                    average_text=subject.average_text,
                    points_only=subject.points_only,
                )
                for mark in marks:
                    container.marks.append(mark)
                new_marks.append(container)
            return new_marks

        for subject in self.subjects._subjects.values():
            marks = [
                m
                for m in subject.marks.get_marks_by_date(date=date, date_to=date_to)
                if m.is_new
            ]
            if marks:
                container = SubjectsBase(
                    id=subject.id,
                    abbr=subject.abbr,
                    name=subject.name,
                    average_text=subject.average_text,
                    points_only=subject.points_only,
                )
                for mark in marks:
                    container.marks.append(mark)
                new_marks.append(container)

        return new_marks
