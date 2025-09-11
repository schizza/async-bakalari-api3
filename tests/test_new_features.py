"""Tests for new features."""

from __future__ import annotations

import pytest

from src.bakalari_api import Bakalari


@pytest.mark.asyncio
async def test_get_grades():
    """Test get_grades."""
    bakalari = Bakalari()
    grades = await bakalari.get_grades()
    assert grades is not None
    assert grades.grades == []


@pytest.mark.asyncio
async def test_get_timetable():
    """Test get_timetable."""
    bakalari = Bakalari()
    timetable = await bakalari.get_timetable()
    assert timetable is not None
    assert timetable.events == []


@pytest.mark.asyncio
async def test_get_homework():
    """Test get_homework."""
    bakalari = Bakalari()
    homework = await bakalari.get_homework()
    assert homework is not None
    assert homework == []
