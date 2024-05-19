"""Test for Komens class."""

import datetime as dt

from aioresponses import aioresponses
import orjson
from src.bakalari_api.bakalari import Bakalari
from src.bakalari_api.const import EndPoint
from src.bakalari_api.komens import Komens, Messages

fs = "http://fake_server"

payload = """
{
  "Messages": [
    {
      "$type": "GeneralMessage",
      "Id": "fake_id1",
      "Title": "",
      "Text": "fake_text_id1",
      "SentDate": "2024-01-01T13:37:28+02:00",
      "Sender": {
        "$type": "Sender",
        "Id": "fake_sender_ID",
        "Type": "teacher",
        "Name": "fake_teacher_name1"
      },
      "Attachments": [
        {
          "$type": "AttachmentInfo",
          "Id": "fake_attachment_id1",
          "Name": "fake_atachement_name1",
          "Type": "fake_type",
          "Size": 12345
        }
      ],
      "Read": true,
      "LifeTime": "ToRead",
      "DateFrom": null,
      "DateTo": null,
      "Confirmed": true,
      "CanConfirm": false,
      "Type": "OBECNA",
      "CanAnswer": true,
      "Hidden": false,
      "CanHide": true,
      "CanDelete": false,
      "RelevantName": "fake_relevant_name1",
      "RelevantPersonType": "fake_relevant_person1"
    },
    {
      "$type": "GeneralMessage",
      "Id": "fake_id2",
      "Title": "",
      "Text": "fake_text_id2",
      "SentDate": "2024-01-05T13:37:28+02:00",
      "Sender": {
        "$type": "Sender",
        "Id": "fake_sender_ID",
        "Type": "teacher",
        "Name": "fake_teacher_name2"
      },
      "Attachments": [],
      "Read": true,
      "LifeTime": "ToRead",
      "DateFrom": null,
      "DateTo": null,
      "Confirmed": true,
      "CanConfirm": false,
      "Type": "OBECNA",
      "CanAnswer": true,
      "Hidden": false,
      "CanHide": true,
      "CanDelete": false,
      "RelevantName": "fake_relevant_name2",
      "RelevantPersonType": "fake_relevant_person2"
    }
   ]}"""


async def test_komens_get_messages():
    """Test the Komens class and its methods."""

    bakalari = Bakalari(fs)
    komens = Komens(bakalari)
    bakalari.credentials.access_token = "token"

    with aioresponses() as m:
        m.post(
            url=fs + EndPoint.KOMENS_UNREAD.get("endpoint"),
            body=payload,
            headers={},
            status=200,
        )

        msgs = await komens.fetch_messages()
        msg = komens.messages.get_message_by_id("fake_id1")
        assert isinstance(komens.messages, Messages)
        assert komens.messages.count_messages() == 2

        assert msg.mid == "fake_id1"
        assert msg.sender == "fake_teacher_name1"
        assert msg.text == "fake_text_id1"
        assert msg.title == ""

        assert (
            str(msgs)
            == """Message id: fake_id1
            title: 
            text: fake_text_id1
            sent: 2024-01-01
            sender: fake_teacher_name1
            attachments: [{'$type': 'AttachmentInfo', 'Id': 'fake_attachment_id1', 'Name': 'fake_atachement_name1', 'Type': 'fake_type', 'Size': 12345}]
Message id: fake_id2
            title: 
            text: fake_text_id2
            sent: 2024-01-05
            sender: fake_teacher_name2
            attachments: []
"""
        )
        assert_msgs = [
            {
                "mid": msg.mid,
                "title": msg.title,
                "text": msg.text,
                "sent": msg.sent,
                "sender": msg.sender,
                "attachments": msg.attachments,
            }
            for msg in msgs
        ]
        assert msgs.json() == orjson.loads(orjson.dumps(assert_msgs))

        msg = komens.messages.get_messages_by_date(dt.date(2024, 1, 1))
        assert msg[0].mid == "fake_id1"

        msg = komens.messages.get_messages_by_date(
            dt.date(2024, 1, 1), to_date=dt.date(2024, 1, 1) + dt.timedelta(days=+5)
        )
        assert isinstance(msg, list)
        assert len(msg) == 2
        assert msg[1].mid == "fake_id2"
        assert (
            str(msg[1])
            == """Message id: fake_id2
            title: 
            text: fake_text_id2
            sent: 2024-01-05
            sender: fake_teacher_name2
            attachments: []"""
        )

        assert (
            repr(msg[0])
            == "<MessageContainer message_id=fake_id1 title= sender=fake_teacher_name1>"
        )

        # JSON
        assert (
            msg[1].as_json()
            == b'{"mid":"fake_id2","title":"","text":"fake_text_id2","sent":"2024-01-05","sender":"fake_teacher_name2","attachments":[]}'
        )

        msg[0].title = "new_set_title"
        assert msg[0].title == "new_set_title"


async def test_komens_count_unread_messages():
    """Test the count_unread_messages method of the Komens class."""

    bakalari = Bakalari(fs)
    komens = Komens(bakalari)
    bakalari.credentials.access_token = "token"

    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.KOMENS_UNREAD_COUNT.get("endpoint"),
            body="50",
            headers={},
            status=200,
        )

        assert await komens.count_unread_messages() == 50


async def test_komens_get_attachment():
    """Test the get_attachment method of the Komens class."""

    bakalari = Bakalari(fs)
    komens = Komens(bakalari)
    bakalari.credentials.access_token = "token"

    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.KOMENS_ATTACHMENT.get("endpoint") + "/1",
            body="content of file",
            headers={
                "Content-type": "application/octet-stream",
                "Content-Disposition": "filename*=utf-8''test-filename",
            },
            status=200,
        )

        test = await komens.get_attachment("1")
        assert test[0] == "test-filename"
        assert test[1] == b"content of file"

    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.KOMENS_ATTACHMENT.get("endpoint") + "/1",
            body="content of file",
            headers={
                "Content-type": "application/octet-stream",
                "Content-Disposition": "filename*=utf-8''test-filename",
            },
            status=400,
        )

        test = await komens.get_attachment("1")
        assert not test
