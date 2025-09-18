"""New features for Bakalari API."""

from __future__ import annotations

from .const import EndPoint
from .datastructure import (
    Grade,
    Grades,
    Homework,
    Subject,
    Timetable,
    TimetableEvent,
)


async def get_grades(self: "Bakalari") -> Grades:
    """Get grades."""
    response = await self.send_auth_request(EndPoint.MARKS)

    # NOTE: The structure of the response is an assumption, as there is no official documentation.
    # Based on other similar projects, it is assumed that the response has a "Subjects" key.
    grades = []
    for subject_data in response.get("Subjects", []):
        subject = Subject(
            id=subject_data.get("Subject", {}).get("Id"),
            name=subject_data.get("Subject", {}).get("Name"),
            abbreviation=subject_data.get("Subject", {}).get("Abbrev"),
        )
        for grade_data in subject_data.get("Marks", []):
            grade = Grade(
                caption=grade_data.get("Caption"),
                value=grade_data.get("MarkText"),
                weight=grade_data.get("Vaha"),
                subject=subject,
                date=grade_data.get("Date"),
                description=grade_data.get("Description"),
            )
            grades.append(grade)

    return Grades(grades=grades)


async def get_timetable(self: "Bakalari") -> Timetable:
    """Get timetable."""
    response = await self.send_auth_request(EndPoint.TIMETABLE)

    # NOTE: The structure of the response is an assumption, as there is no official documentation.
    # Based on other similar projects, it is assumed that the response has a "Days" key.
    events = []
    for day_data in response.get("Days", []):
        for event_data in day_data.get("Hours", []):
            event = TimetableEvent(
                subject=Subject(
                    id=event_data.get("Subject", {}).get("Id"),
                    name=event_data.get("Subject", {}).get("Name"),
                    abbreviation=event_data.get("Subject", {}).get("Abbrev"),
                ),
                teacher=event_data.get("Teacher", {}).get("Name"),
                room=event_data.get("Room", {}).get("Name"),
                group=event_data.get("Group", {}).get("Name"),
                time_from=event_data.get("BeginTime"),
                time_to=event_data.get("EndTime"),
                day=day_data.get("Date"),
            )
            events.append(event)

    return Timetable(events=events)


async def get_homework(self: "Bakalari") -> list[Homework]:
    """Get homework."""
    response = await self.send_auth_request(EndPoint.HOMEWORK)

    # NOTE: The structure of the response is an assumption, as there is no official documentation.
    # Based on other similar projects, it is assumed that the response has a "Homeworks" key.
    homeworks = []
    for homework_data in response.get("Homeworks", []):
        homework = Homework(
            subject=Subject(
                id=homework_data.get("Subject", {}).get("Id"),
                name=homework_data.get("Subject", {}).get("Name"),
                abbreviation=homework_data.get("Subject", {}).get("Abbrev"),
            ),
            assigned_date=homework_data.get("DateStart"),
            due_date=homework_data.get("DateEnd"),
            description=homework_data.get("Content"),
            completed=homework_data.get("Done"),
        )
        homeworks.append(homework)

    return homeworks
