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
    def get_marks_by_date(self, date: datetime, date_to: datetime) -> list[MarksBase]:
        ...
    @overload
    def get_marks_by_date(self, date: datetime) -> list[MarksBase]:
        ...
    @overload
    def get_marks_by_date(self, subject_id: str, date: datetime, date_to: datetime) -> list[MarksBase]:
        ...
    @overload
    def get_marks_by_date(self, subject_id: str, date: datetime) -> list[MarksBase]:
        ...

    def get_marks_by_date(self , subject_id: str | None = None, date: datetime | None = None, date_to: datetime | None = None) -> list[MarksBase]:
        """Get marks by date or date range. Or for subject by date or date range."""

        if subject_id is not None:
            if date_to is not None:
                return [mark for mark in self._data.values() if mark.subject_id == subject_id and mark.date.date() >= date.date() and mark.date <= date_to.date()]
            return [mark for mark in self._data.values() if mark.subject_id == subject_id and mark.date.date() == date.date()]

        if date_to is not None:
            return [mark for mark in self._data.values() if mark.date.date() >= date.date() and mark.date <= date_to.date()]
        return [mark for mark in self._data.values() if mark.date.date() == date.date()]
        
        
    def get(self, id: str) -> MarksBase:
        """Get marks."""
        return self._data.get(id, None)

    def __repr__(self) -> str:
        """Representation of MarksRegistry."""

        return (
            f"<MarksRegistry id={data.id} date={data.date} caption={data.caption} theme={data.theme} marktext={data.marktext} teacher={data.teacher} subject_id={data.subject_id} is_new={data.is_new} is_points={data.is_points} points_text={data.points_text} max_points={data.max_points}>"
            for data in self._data
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
            f"----\n")

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

    async def get_marks(self, subject_id: str) -> list[MarksBase]:
        """Get marks for subject."""

        return list(self.subjects.get_subject(subject_id).marks)

    async def get_new_marks(self) -> list[SubjectsBase]:
        """Get new marks for subject."""

        new_marks: list[SubjectsBase] = []

        for subject in self.subjects._subjects.values():
            if len(found := subject.marks.find_new_marks()) != 0:
                new_marks.append(SubjectsBase(
                    id=subject.id,
                    abbr=subject.abbr,
                    name=subject.name,
                    average_text=subject.average_text,
                    points_only=subject.points_only,
                ))
                for mark in found:
                    new_marks[-1].marks.append(mark)
        return new_marks

    @overload
    async def get_new_marks_by_date(self, date: datetime = ..., *, date_to: datetime, subject_id: str) -> list[SubjectsBase]:
        ...

    @overload
    async def get_new_marks_by_date(self, date: datetime = ..., date_to: datetime = ..., *, subject_id: str) -> list[SubjectsBase]:
        ...
    @overload
    async def get_new_marks_by_date(self,  date: datetime = ..., date_to: datetime = ..., subject_id: str = ...) -> list[SubjectsBase]:
        ...
    @overload
    async def get_new_marks_by_date(self, date: datetime = ..., subject_id: str = ..., *, date_to: datetime) -> list[SubjectsBase]:
        ...

    async def get_new_marks_by_date(
        self,
        date: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None  = None,
        ) -> list[SubjectsBase]:
        """Get marks by date or date range. Or for subject by date or date range."""

        new_marks: list[SubjectsBase] = []

        if subject_id is not None:
            if date_to is not None:
                marks = self.subjects.get_subject(subject_id).marks.get_marks_by_date(subject_id, date, date_to)
                for mark in marks:
                    new_marks[-1].marks.append(mark)
            else:
                marks = self.subjects.get_subject(subject_id).marks.get_marks_by_date(subject_id, date)
                for mark in marks:
                    new_marks[-1].marks.append(mark)

        if date_to is not None:
            for subject in self.subjects._subjects.values():
                marks = self.subjects.get_subject(subject.id).marks.get_marks_by_date(subject.id, date, date_to)
                for mark in marks:
                    new_marks[-1].marks.append(mark)
        else:
            for subject in self.subjects._subjects.values():
                # marks = self.subjects.get_subject.marks.get_marks_by_date(subject.id, date)
                marks = self.subjects.get_subject(subject.id).marks.get_marks_by_date(subject.id, date)
                if marks:
                    new_marks.append(SubjectsBase(
                        id=subject.id,
                        abbr=subject.abbr,
                        name=subject.name,
                        average_text=subject.average_text,
                        points_only=subject.points_only,
                    ))
                    for mark in marks:
                        new_marks[-1].marks.append(mark)
                # if len(found := self._subjects.get_marks(subject_id).marks.date.date() >= date.date() and self._subjects.get_marks(subject_id).marks.date <= date_to.date()) != 0:
                #        marks.date.date() >= date.date() and subject.marks.date <= date_to.date()) != 0:
                #     new_marks.append(SubjectsBase(
                #         id=subject.id,
                #         abbr=subject.abbr,
                #         name=subject.name,
                #         average_text=subject.average_text,
                #         points_only=subject.points_only,
                #     ))
                # for mark in found:
                #     new_marks[-1].marks.append(mark)

        return new_marks
