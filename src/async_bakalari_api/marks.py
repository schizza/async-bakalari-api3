"""High level service for working with Bakaláři marks."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from operator import attrgetter
from typing import Any, Callable, Iterable, Literal

from dateutil import parser

from .bakalari import Bakalari
from .const import EndPoint
from .logger_api import api_logger
from .marks_models import (
    FlatMark,
    FlatSnapshot,
    Mark,
    MarkOption,
    MarksDataset,
    Subject,
    SubjectSummary,
)

log = api_logger("Bakalari API").get()


class SubjectBuilder:
    """Mutable helper used while parsing payloads."""

    def __init__(
        self,
        *,
        subject_id: str,
        abbr: str,
        name: str,
        average_text: str,
        points_only: bool,
    ) -> None:
        self.id = subject_id
        self.abbr = abbr
        self.name = name
        self.average_text = average_text
        self.points_only = points_only
        self._marks: list[Mark] = []

    def add_mark(self, mark: Mark) -> None:
        self._marks.append(mark)

    def build(self) -> Subject:
        return Subject(
            id=self.id,
            abbr=self.abbr,
            name=self.name,
            average_text=self.average_text,
            points_only=self.points_only,
            marks=tuple(sorted(self._marks, key=attrgetter("date"))),
        )


class MarksAssembler:
    """Builder that constructs immutable :class:`MarksDataset`."""

    def __init__(self) -> None:
        self._options: dict[str, MarkOption] = {}
        self._subjects: dict[str, SubjectBuilder] = {}

    def add_option(self, *, option_id: str, abbr: str, text: str) -> None:
        if option_id not in self._options:
            self._options[option_id] = MarkOption(id=option_id, abbr=abbr, text=text)

    def ensure_subject(
        self,
        *,
        subject_id: str,
        abbr: str,
        name: str,
        average_text: str,
        points_only: bool,
    ) -> SubjectBuilder:
        subject = self._subjects.get(subject_id)
        if subject is None:
            subject = SubjectBuilder(
                subject_id=subject_id,
                abbr=abbr,
                name=name,
                average_text=average_text,
                points_only=points_only,
            )
            self._subjects[subject_id] = subject
        return subject

    def add_mark(
        self,
        *,
        mark_id: str,
        mark_date: datetime,
        caption: str | None,
        theme: str | None,
        mark_text_id: str | None,
        teacher: str | None,
        subject_id: str,
        is_new: bool,
        is_points: bool,
        points_text: str | None,
        max_points: int | None,
    ) -> None:
        subject = self._subjects.get(subject_id)
        if subject is None:
            log.warning(f"Subject {subject_id} not found for mark {mark_id}")
            return

        option = None
        if mark_text_id:
            option = self._options.get(mark_text_id)
            if option is None:
                log.warning(
                    "MarkOptions not found for MarkText=%r; using placeholder",
                    mark_text_id,
                )
                option = MarkOption(
                    id=mark_text_id,
                    abbr=mark_text_id,
                    text=mark_text_id,
                )
                self._options[mark_text_id] = option

        mark = Mark(
            id=mark_id,
            date=mark_date,
            caption=caption,
            theme=theme,
            mark_option=option,
            teacher=teacher,
            subject_id=subject_id,
            is_new=is_new,
            is_points=is_points,
            points_text=points_text,
            max_points=max_points,
        )
        subject.add_mark(mark)

    def build(self) -> MarksDataset:
        return MarksDataset({sid: subj.build() for sid, subj in self._subjects.items()})


class MarksService:
    """Pure service operating on immutable :class:`MarksDataset`."""

    def __init__(self, dataset: MarksDataset) -> None:
        self.dataset = dataset

    def _iter_subjects(self, subject_id: str | None) -> Iterable[Subject]:
        if subject_id is None:
            return self.dataset.iter_subjects()
        subject = self.dataset.get_subject(subject_id)
        return (subject,) if subject else tuple()

    @staticmethod
    def _mark_in_range(
        mark: Mark,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> bool:
        if date_from is None:
            return True
        end = date_to or date_from
        mdate = mark.date.date()
        return date_from.date() <= mdate <= end.date()

    def _filter_marks(
        self,
        marks: Iterable[Mark],
        *,
        date_from: datetime | None,
        date_to: datetime | None,
        predicate: Callable[[Mark], bool] | None,
    ) -> list[Mark]:
        items = [
            mark
            for mark in marks
            if self._mark_in_range(mark, date_from=date_from, date_to=date_to)
        ]
        if predicate is not None:
            items = [mark for mark in items if predicate(mark)]
        return items

    def iter_grouped(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
    ) -> Iterable[tuple[Subject, list[Mark]]]:
        for subject in self._iter_subjects(subject_id):
            if subject is None:
                continue
            filtered = self._filter_marks(
                subject.marks,
                date_from=date_from,
                date_to=date_to,
                predicate=predicate,
            )
            if filtered:
                yield subject, filtered

    def get_marks_all(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
    ) -> list[Subject]:
        groups: list[Subject] = []
        for subject, marks in self.iter_grouped(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
        ):
            groups.append(replace(subject, marks=tuple(marks)))
        return groups

    def get_new_marks(self) -> list[Subject]:
        return self.get_marks_all(predicate=lambda mark: mark.is_new)

    def get_new_marks_by_date(
        self,
        *,
        date_from: datetime,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> list[Subject]:
        return self.get_marks_all(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=lambda mark: mark.is_new,
        )

    def _to_flat_mark(self, subject: Subject, mark: Mark) -> FlatMark:
        mark_text = mark.mark_option.text if mark.mark_option else None
        theme = (mark.theme or "").strip() or None
        return FlatMark(
            id=mark.id,
            date=mark.date,
            subject_id=subject.id,
            subject_abbr=subject.abbr,
            subject_name=subject.name,
            caption=mark.caption,
            theme=theme,
            mark_text=mark_text,
            is_new=mark.is_new,
            is_points=mark.is_points,
            points_text=mark.points_text,
            max_points=mark.max_points,
            teacher=mark.teacher,
        )

    def get_flat(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> list[FlatMark]:
        items: list[FlatMark] = []
        for subject, marks in self.iter_grouped(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
        ):
            items.extend(self._to_flat_mark(subject, mark) for mark in marks)
        items.sort(key=attrgetter("date"), reverse=(order == "desc"))
        return items

    def get_snapshot(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> FlatSnapshot:
        grouped: dict[str, tuple[FlatMark, ...]] = {}
        flat_items: list[FlatMark] = []
        for subject, marks in self.iter_grouped(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
        ):
            flat_marks = tuple(self._to_flat_mark(subject, mark) for mark in marks)
            grouped[subject.id] = tuple(
                sorted(flat_marks, key=attrgetter("date"), reverse=(order == "desc"))
            )
            flat_items.extend(flat_marks)

        flat_items.sort(key=attrgetter("date"), reverse=(order == "desc"))

        summaries = {
            subject.id: SubjectSummary(
                id=subject.id,
                abbr=subject.abbr,
                name=subject.name,
                average_text=subject.average_text,
                points_only=subject.points_only,
            )
            for subject in self._iter_subjects(subject_id)
            if subject is not None
        }

        return FlatSnapshot(
            subjects=summaries,
            marks_grouped=grouped,
            marks_flat=tuple(flat_items),
        )


class Marks:
    """Facade combining Bakaláři client with :class:`MarksService`."""

    def __init__(self, bakalari: Bakalari):
        self.bakalari = bakalari
        self._service: MarksService | None = None

    def _require_service(self) -> MarksService:
        if self._service is None:
            raise RuntimeError("fetch_marks must be called before accessing data")
        return self._service

    async def fetch_marks(self) -> None:
        """Fetch marks from Bakaláři and populate immutable dataset."""

        response: Any = await self.bakalari.send_auth_request(EndPoint.MARKS)
        assembler = MarksAssembler()

        for option in response.get("MarkOptions", []):
            assembler.add_option(
                option_id=option.get("Id", ""),
                abbr=option.get("Abbrev", ""),
                text=option.get("Name", ""),
            )

        for subject in response.get("Subjects", []):
            subj_meta = subject.get("Subject", {})
            assembler.ensure_subject(
                subject_id=subj_meta.get("Id", ""),
                abbr=subj_meta.get("Abbrev", ""),
                name=subj_meta.get("Name", ""),
                average_text=subject.get("AverageText", ""),
                points_only=subject.get("PointsOnly", False),
            )
            for mark in subject.get("Marks", []):
                assembler.add_mark(
                    mark_id=mark.get("Id", ""),
                    mark_date=parser.parse(mark.get("MarkDate")),
                    caption=mark.get("Caption"),
                    theme=mark.get("Theme"),
                    mark_text_id=mark.get("MarkText"),
                    teacher=mark.get("Teacher"),
                    subject_id=mark.get("SubjectId", ""),
                    is_new=mark.get("IsNew", False),
                    is_points=mark.get("IsPoints", False),
                    points_text=mark.get("PointsText"),
                    max_points=mark.get("MaxPoints"),
                )

        self._service = MarksService(assembler.build())

    async def get_subjects(self) -> list[Subject]:
        return list(self._require_service().dataset.iter_subjects())

    async def get_marks_by_subject(self, subject_id: str) -> list[Mark]:
        subject = self._require_service().dataset.get_subject(subject_id)
        return list(subject.marks) if subject else []

    async def get_new_marks(self) -> list[Subject]:
        return self._require_service().get_new_marks()

    async def get_new_marks_by_date(
        self,
        date_from: datetime,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> list[Subject]:
        return self._require_service().get_new_marks_by_date(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
        )

    async def get_marks_all(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> list[Subject]:
        return self._require_service().get_marks_all(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
        )

    async def format_all_marks(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
    ) -> str:
        groups = await self.get_marks_all(
            date_from=date_from, date_to=date_to, subject_id=subject_id
        )
        lines: list[str] = []
        for subject in groups:
            header = (
                f"{subject.name} ({subject.abbr}) | average: {subject.average_text} | "
                f"points_only: {subject.points_only}"
            )
            lines.append(header)
            lines.append("-" * len(header))
            for mark in subject.marks:
                mark_text = mark.mark_option.text if mark.mark_option else ""
                caption = mark.caption or ""
                line = f"  [{mark.date.date()}] {caption} -> {mark_text}"
                if mark.is_new:
                    line += " [NEW]"
                lines.append(line)
                if mark.theme:
                    lines.append(f"    theme: {mark.theme.strip()}")
                if mark.is_points:
                    suffix = (
                        f"{mark.points_text} / {mark.max_points}"
                        if mark.max_points is not None
                        else f"{mark.points_text}"
                    )
                    lines.append(f"    points: {suffix}")
        return "\n".join(lines)

    def get_subjects_map(self) -> dict[str, Subject]:
        service = self._require_service()
        return {subject.id: subject for subject in service.dataset.iter_subjects()}

    def iter_grouped(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
    ) -> Iterable[tuple[Subject, list[Mark]]]:
        return self._require_service().iter_grouped(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
        )

    async def get_flat(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> list[FlatMark]:
        return self._require_service().get_flat(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
            order=order,
        )

    async def get_snapshot(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
        order: Literal["asc", "desc"] = "desc",
        to_dict: bool = False,
    ) -> FlatSnapshot | dict[str, Any]:
        snapshot = self._require_service().get_snapshot(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
            order=order,
        )
        return snapshot.to_dict() if to_dict else snapshot

    async def get_snapshot_for_school_year(
        self,
        *,
        school_year: tuple[datetime, datetime],
        order: Literal["asc", "desc"] = "desc",
    ) -> FlatSnapshot | dict[str, Any]:
        start, end = school_year
        return await self.get_snapshot(date_from=start, date_to=end, order=order)

    async def diff_ids(
        self,
        previous_ids: set[str],
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[Mark], bool] | None = None,
    ) -> tuple[set[str], list[FlatMark]]:
        flat = await self.get_flat(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            predicate=predicate,
            order="desc",
        )
        curr_ids = {mark.id for mark in flat}
        new_ids = curr_ids - previous_ids
        new_items = [mark for mark in flat if mark.id in new_ids]
        return new_ids, new_items

