r"""Regression tests for null / missing fields in the Bakaláři /marks response.

Real bug report (zs-zarubova, child RGU0U5, 04/2026):

    ERROR ... Failed while get_marks_snapshot:
      expected string or bytes-like object, got 'NoneType'

HTTP call returned 200, so the payload arrived fine — it blew up inside the
parser. The suspect is ``re.search(r"\\d+...", None)`` in
``Marks.sanitize_number`` when a subject has ``"AverageText": null``
(a typical value when a subject has too few marks to compute an average).

These tests lock in the expected tolerant behaviour for every edge case
we can think of. Before the fix, the ones marked *crashes_current_impl*
must FAIL to prove the repro is correct; after the fix, all must PASS.
"""

from __future__ import annotations

import logging
from typing import Any

from aioresponses import aioresponses
from src.async_bakalari_api.bakalari import Bakalari
from src.async_bakalari_api.const import EndPoint
from src.async_bakalari_api.datastructure import Credentials
from src.async_bakalari_api.marks import Marks

FS = "http://fake_server"
CRED = Credentials(access_token="token", refresh_token="refresh_token")


# ---------- fixtures -------------------------------------------------------


def _base_payload() -> dict[str, Any]:
    """Minimal valid payload with exactly one subject and one mark.

    Tests take this and corrupt one field at a time to isolate each bug.
    """
    return {
        "MarkOptions": [
            {"Id": "1", "Abbrev": "Jedna", "Name": "1"},
        ],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.5",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "m1",
                        "MarkDate": "2026-04-10T12:00:00+00:00",
                        "Caption": "Písemka",
                        "Theme": "Zlomky",
                        "MarkText": "1",
                        "Teacher": "NN",
                        "SubjectId": "101",
                        "IsNew": True,
                        "IsPoints": False,
                        "PointsText": None,
                        "MaxPoints": None,
                        "MarkConfirmationState": "Confirmed",
                    }
                ],
            }
        ],
    }


async def _run_fetch(payload: dict[str, Any]) -> Marks:
    """Run the real fetch_marks pipeline against a mocked HTTP response."""
    bakalari = Bakalari(FS, credentials=CRED)
    marks = Marks(bakalari)
    with aioresponses() as m:
        m.get(
            url=FS + EndPoint.MARKS.get("endpoint"),
            payload=payload,
            headers={},
            status=200,
        )
        await marks.fetch_marks()
    await bakalari.__aexit__()
    return marks


# ---------- baseline -------------------------------------------------------


async def test_valid_payload_still_works():
    """Sanity: untouched payload loads without errors (baseline)."""
    marks = await _run_fetch(_base_payload())
    subjects = await marks.get_subjects()
    assert len(subjects) == 1
    assert subjects[0].id == "101"

    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "1"
    assert summary["total_marks"] == "1"


# ---------- the primary repro ---------------------------------------------


async def test_null_average_text_crashes_current_impl():
    """``AverageText: null`` must not blow up the snapshot.

    This is the exact user-reported bug. Current ``sanitize_number``
    passes ``None`` to ``re.search`` and raises TypeError, which bubbles
    up to the @api_call decorator and nukes the whole child's snapshot.
    """
    payload = _base_payload()
    payload["Subjects"][0]["AverageText"] = None

    marks = await _run_fetch(payload)  # must not raise

    # Subject must still be present with an empty (but valid) average_text.
    subjects = await marks.get_subjects()
    assert len(subjects) == 1
    assert subjects[0].id == "101"
    assert subjects[0].average_text in ("", None) or isinstance(
        subjects[0].average_text, str
    )

    # Summary must not raise either; the subject with null average contributes 0.
    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "1"
    assert summary["total_marks"] == "1"
    # Averages may be 0 or some valid number; just ensure it's stringifiable.
    assert isinstance(summary["avg"], str)
    assert isinstance(summary["wavg"], str)


async def test_average_text_key_missing_is_tolerated():
    """``AverageText`` key absent entirely (currently OK via .get default)."""
    payload = _base_payload()
    del payload["Subjects"][0]["AverageText"]

    marks = await _run_fetch(payload)
    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "1"


# ---------- MarkOptions.Name null -----------------------------------------


async def test_null_mark_name_in_options_crashes_current_impl():
    """``MarkOptions[i].Name: null`` propagates None into MarkOptionsBase.text.

    Which later crashes ``sanitize_number`` inside ``get_all_marks_summary``.
    """
    payload = _base_payload()
    payload["MarkOptions"][0]["Name"] = None

    marks = await _run_fetch(payload)
    summary = await marks.get_all_marks_summary()  # must not raise
    assert summary["subjects"] == "1"


async def test_mark_options_list_null():
    """``MarkOptions: null`` at top level must not crash parse_marks_options."""
    payload = _base_payload()
    payload["MarkOptions"] = None

    marks = await _run_fetch(payload)  # must not raise
    # The mark with MarkText="1" will fall through to the placeholder branch.
    subjects = await marks.get_subjects()
    assert len(subjects) == 1


# ---------- broken individual marks ---------------------------------------


async def test_missing_mark_date_crashes_current_impl():
    """A mark with ``MarkDate: null`` must be skipped, not abort the subject.

    Current impl calls ``dateutil.parser.parse(None)`` which raises TypeError;
    the whole asyncio.gather then surfaces the exception and fetch_marks
    fails for the entire child.
    """
    payload = _base_payload()

    payload["Subjects"][0]["Marks"].append(
        {
            "Id": "m_ok",
            "MarkDate": "2026-04-12T10:00:00+00:00",
            "Caption": "Ok písemka",
            "Theme": "Zlomky",
            "MarkText": "1",
            "Teacher": "NN",
            "SubjectId": "101",
            "IsNew": False,
            "IsPoints": False,
            "PointsText": None,
            "MaxPoints": None,
            "MarkConfirmationState": "Confirmed",
        }
    )
    # Break the first mark.
    payload["Subjects"][0]["Marks"][0]["MarkDate"] = None

    marks = await _run_fetch(payload)  # must not raise
    assert len(await marks.get_subjects()) == 1

    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "1"
    assert summary["total_marks"] == "1"  # one is skipped, one suvived


async def test_unparseable_mark_date_is_skipped():
    """Garbage string in MarkDate must be skipped, not crash."""
    payload = _base_payload()
    payload["Subjects"][0]["Marks"].append(
        {
            "Id": "m_ok",
            "MarkDate": "2026-04-12T10:00:00+00:00",
            "Caption": "Ok písemka",
            "Theme": "",
            "MarkText": "1",
            "Teacher": "NN",
            "SubjectId": "101",
            "IsNew": False,
            "IsPoints": False,
            "PointsText": None,
            "MaxPoints": None,
            "MarkConfirmationState": "Confirmed",
        }
    )
    payload["Subjects"][0]["Marks"][0]["MarkDate"] = "not-a-date"

    marks = await _run_fetch(payload)
    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "1"


async def test_marks_field_null_crashes_current_impl():
    """A subject with ``Marks: null`` (instead of []) must not crash.

    Current impl does ``for mark in subjects["Marks"]:`` which raises
    TypeError when the value is None.
    """
    payload = _base_payload()
    payload["Subjects"][0]["Marks"] = None

    marks = await _run_fetch(payload)  # must not raise
    assert len(await marks.get_subjects()) == 1

    # No marks, so summary still loads and reports the subject with zero marks.
    summary = await marks.get_all_marks_summary()
    assert summary["subjects"] == "0"
    assert summary["total_marks"] == "0"


async def test_marks_field_missing():
    """A subject without the ``Marks`` key at all.

    Current impl uses ``subjects["Marks"]`` (not .get) and raises KeyError.
    """
    payload = _base_payload()
    del payload["Subjects"][0]["Marks"]

    marks = await _run_fetch(payload)  # must not raise
    assert len(await marks.get_subjects()) == 1


# ---------- broken subject wrapper ----------------------------------------


async def test_missing_subject_key_crashes_current_impl():
    """Subject entry without inner ``Subject`` key must not crash.

    Current impl does ``subjects["Subject"].get("Id")`` → KeyError.
    """
    payload = _base_payload()
    del payload["Subjects"][0]["Subject"]

    _ = await _run_fetch(payload)  # must not raise
    # Without a proper Subject block we may or may not register the subject —
    # implementations can choose; the important thing is we didn't fail.
    # We only assert fetch_marks itself is non-fatal.


async def test_subject_inner_null_crashes_current_impl():
    """``Subject: null`` must not crash either (current impl calls .get on None)."""
    payload = _base_payload()
    payload["Subjects"][0]["Subject"] = None

    _ = await _run_fetch(payload)  # must not raise


async def test_one_broken_subject_does_not_block_the_good_one():
    """Bad subject in a batch must not prevent good subjects from loading.

    Current impl uses ``asyncio.gather(*tasks)`` without ``return_exceptions``,
    so the first crash cancels the whole batch and the child ends up with
    zero subjects — exactly the zs-zarubova symptom.
    """
    payload = _base_payload()
    # Keep the good subject, add a poisoned one that will explode on parse.
    payload["Subjects"].append(
        {
            "Subject": {"Id": "202", "Abbrev": "AJ", "Name": "Angličtina"},
            "AverageText": None,  # trigger #1
            "PointsOnly": False,
            "Marks": [
                {
                    "Id": "bad",
                    "MarkDate": None,  # trigger #2
                    "MarkText": "1",
                    "SubjectId": "202",
                }
            ],
        }
    )

    marks = await _run_fetch(payload)  # must not raise

    subjects_ids = {s.id for s in await marks.get_subjects()}
    # The good subject MUST survive regardless of the broken one's fate.
    assert "101" in subjects_ids


# ---------- top-level response oddities -----------------------------------


async def test_subjects_field_null_is_tolerated():
    """``Subjects: null`` at top-level: parsing must degrade gracefully."""
    payload = _base_payload()
    payload["Subjects"] = None

    marks = await _run_fetch(payload)  # must not raise
    assert await marks.get_subjects() == []


async def test_empty_response_object():
    """Server returns ``{}`` (no keys). Must degrade to empty snapshot."""
    marks = await _run_fetch({})  # must not raise
    assert await marks.get_subjects() == []
    summary = await marks.get_all_marks_summary()
    assert summary["total_marks"] == "0"


# ---------- bonus: what the downstream sees -------------------------------


async def test_snapshot_with_null_average_text_returns_usable_shape():
    """The HA integration reads `snapshot['subjects']`.

    that dict must be populated even when some AverageText is null. This is the direct cause
    of ``No subjects found for child ...`` in the HA log.
    """

    payload = _base_payload()
    payload["Subjects"][0]["AverageText"] = None

    marks = await _run_fetch(payload)
    snapshot = await marks.get_snapshot(to_dict=True)
    # subjects dict must contain our one subject
    assert "101" in snapshot["subjects"]
    # marks_flat must list the one mark we parsed
    assert len(snapshot["marks_flat"]) == 1


async def test_fetch_marks_returns_early_on_non_dict_response(caplog):
    """Test early return.

    If the marks endpoint returns a non-dict payload (list/str/None),
    fetch_marks must log a warning and return without touching the registry.

    Covers the ``if not isinstance(response, dict): return`` guard.
    """

    bakalari = Bakalari(FS, credentials=CRED)
    marks = Marks(bakalari)

    with aioresponses() as m:
        # Server returns a JSON array instead of the expected object
        m.get(
            url=FS + EndPoint.MARKS.get("endpoint"),
            payload=["unexpected", "list", "payload"],
            headers={},
            status=200,
        )
        with caplog.at_level(logging.WARNING, logger="src.async_bakalari_api.marks"):
            await marks.fetch_marks()  # must not raise

    await bakalari.__aexit__()

    # Early-return: no subjects parsed, no options registered
    assert await marks.get_subjects() == []
    assert str(marks.marksoptions) == ""

    # The warning was emitted
    assert any("unexpected response type" in rec.message for rec in caplog.records), (
        f"expected 'unexpected response type' warning, got: {[r.message for r in caplog.records]}"
    )


async def test_fetch_marks_returns_early_on_string_response(caplog):
    """Same guard, different non-dict shape (JSON string)."""

    bakalari = Bakalari(FS, credentials=CRED)
    marks = Marks(bakalari)

    with aioresponses() as m:
        m.get(
            url=FS + EndPoint.MARKS.get("endpoint"),
            payload="not a dict",
            headers={},
            status=200,
        )
        with caplog.at_level(logging.WARNING, logger="src.async_bakalari_api.marks"):
            await marks.fetch_marks()

    await bakalari.__aexit__()
    assert await marks.get_subjects() == []
    assert any("unexpected response type" in rec.message for rec in caplog.records)


async def test_fetch_marks_logs_when_subject_task_raises(monkeypatch, caplog):
    """Test task raise error.

    If a ``_parse_subjects`` task raises, the error is collected by
    ``asyncio.gather(return_exceptions=True)`` and logged as a warning;
    remaining subjects continue to be parsed.

    Covers the ``log.warning("fetch_marks: subject parse failed: ...")`` branch.
    """

    bakalari = Bakalari(FS, credentials=CRED)
    marks = Marks(bakalari)

    # Patch _parse_subjects so the FIRST call raises, the second succeeds.
    original = marks._parse_subjects
    call_count = {"n": 0}

    async def flaky_parse(subjects):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("boom-in-parse-subjects")
        await original(subjects)

    monkeypatch.setattr(marks, "_parse_subjects", flaky_parse)

    # Payload with two subjects — the first one triggers the raise,
    # the second one must still land in the registry.
    payload = {
        "MarkOptions": [{"Id": "1", "Abbrev": "1", "Name": "1"}],
        "Subjects": [
            {
                "Subject": {"Id": "101", "Abbrev": "MAT", "Name": "Matematika"},
                "AverageText": "1.0",
                "PointsOnly": False,
                "Marks": [],
            },
            {
                "Subject": {"Id": "202", "Abbrev": "AJ", "Name": "Angličtina"},
                "AverageText": "1.5",
                "PointsOnly": False,
                "Marks": [
                    {
                        "Id": "m1",
                        "MarkDate": "2026-04-10T10:00:00+00:00",
                        "MarkText": "1",
                        "SubjectId": "202",
                        "MarkConfirmationState": "Confirmed",
                    }
                ],
            },
        ],
    }

    with aioresponses() as m:
        m.get(
            url=FS + EndPoint.MARKS.get("endpoint"),
            payload=payload,
            headers={},
            status=200,
        )
        with caplog.at_level(logging.WARNING, logger="src.async_bakalari_api.marks"):
            await marks.fetch_marks()  # must not raise

    await bakalari.__aexit__()

    # First task raised, second succeeded
    assert call_count["n"] == 2
    subject_ids = {s.id for s in await marks.get_subjects()}
    assert "202" in subject_ids  # second subject loaded
    assert "101" not in subject_ids  # first subject was the failing one

    # The warning path ran
    assert any(
        "subject parse failed" in rec.message
        and "boom-in-parse-subjects" in rec.message
        for rec in caplog.records
    ), (
        f"expected subject parse failure warning, got: {[r.message for r in caplog.records]}"
    )


async def test_empty_string_mark_text_resolves_to_empty_id_option():
    """Test empry string ID.

    If MarkOptions has an entry with Id="" (or null normalized to ""),
    a mark with MarkText="" must resolve to THAT entry, not to a blank
    placeholder. Regression: the ``if raw_mt_id`` guard in _parse_subjects
    used to bypass the lookup for empty strings.
    """
    payload = _base_payload()
    # Registry: one normal entry + one with empty id (simulating Id: null
    # after the or-"" normalization in _parse_marks_options)
    payload["MarkOptions"] = [
        {"Id": "1", "Abbrev": "Jedna", "Name": "1"},
        {"Id": "", "Abbrev": "NH", "Name": "nehodnoceno"},
    ]
    # The mark references the empty-id entry
    payload["Subjects"][0]["Marks"][0]["MarkText"] = ""

    marks = await _run_fetch(payload)

    # Pick up the mark we just parsed and check its resolved marktext
    subjects = await marks.get_subjects()
    assert len(subjects) == 1
    all_marks = list(subjects[0].marks)
    assert len(all_marks) == 1

    mt = all_marks[0].marktext
    assert mt is not None
    assert mt.abbr == "NH"  # resolved, not placeholder
    assert mt.text == "nehodnoceno"  # resolved, not placeholder
