"""Data layer for marks domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class MarkOption:
    """Metadata describing a mark grade option."""

    id: str
    abbr: str
    text: str


@dataclass(frozen=True, slots=True)
class Mark:
    """Immutable representation of a mark."""

    id: str
    date: datetime
    caption: str | None
    theme: str | None
    mark_option: MarkOption | None
    teacher: str | None
    subject_id: str
    is_new: bool
    is_points: bool
    points_text: str | None
    max_points: int | None


@dataclass(frozen=True, slots=True)
class Subject:
    """Immutable representation of a subject including its marks."""

    id: str
    abbr: str
    name: str
    average_text: str
    points_only: bool
    marks: tuple[Mark, ...]


@dataclass(frozen=True, slots=True)
class MarksDataset:
    """Immutable container for all parsed marks."""

    subjects: Mapping[str, Subject]

    def __post_init__(self) -> None:  # pragma: no cover - trivial guard
        object.__setattr__(self, "subjects", MappingProxyType(dict(self.subjects)))

    def get_subject(self, subject_id: str) -> Subject | None:
        """Return subject by identifier."""

        return self.subjects.get(subject_id)

    def iter_subjects(self) -> Sequence[Subject]:
        """Return a view over subjects."""

        return tuple(self.subjects.values())


@dataclass(frozen=True, slots=True)
class SubjectSummary:
    """Normalized summary for snapshot output."""

    id: str
    abbr: str
    name: str
    average_text: str
    points_only: bool


@dataclass(frozen=True, slots=True)
class FlatMark:
    """Subject enriched mark."""

    id: str
    date: datetime
    subject_id: str
    subject_abbr: str
    subject_name: str
    caption: str | None
    theme: str | None
    mark_text: str | None
    is_new: bool
    is_points: bool
    points_text: str | None
    max_points: int | None
    teacher: str | None

    def as_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with ISO timestamp."""

        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "subject_id": self.subject_id,
            "subject_abbr": self.subject_abbr,
            "subject_name": self.subject_name,
            "caption": self.caption,
            "theme": self.theme,
            "mark_text": self.mark_text,
            "is_new": self.is_new,
            "is_points": self.is_points,
            "points_text": self.points_text,
            "max_points": self.max_points,
            "teacher": self.teacher,
        }


@dataclass(frozen=True, slots=True)
class FlatSnapshot:
    """Normalized snapshot returned by :class:`MarksService`."""

    subjects: Mapping[str, SubjectSummary]
    marks_grouped: Mapping[str, tuple[FlatMark, ...]]
    marks_flat: tuple[FlatMark, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot into primitive dictionaries and lists."""

        return {
            "subjects": {
                sid: {
                    "id": summary.id,
                    "abbr": summary.abbr,
                    "name": summary.name,
                    "average_text": summary.average_text,
                    "points_only": summary.points_only,
                }
                for sid, summary in self.subjects.items()
            },
            "marks_grouped": {
                sid: [mark.as_dict() for mark in marks]
                for sid, marks in self.marks_grouped.items()
            },
            "marks_flat": [mark.as_dict() for mark in self.marks_flat],
        }

