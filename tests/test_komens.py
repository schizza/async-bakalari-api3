"""Test for Komens class."""

import datetime as dt

from aioresponses import aioresponses
from async_bakalari_api.datastructure import Credentials
from async_bakalari_api.bakalari import Bakalari
from async_bakalari_api.const import EndPoint
from async_bakalari_api.komens import AttachmentsRegistry, Komens, Messages

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

payload_unread = """{
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
      "Read": false,
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

cred:Credentials = Credentials(access_token="token", refresh_token="ref_token")


def test_attributes_Att_registry():
    """Test the AttachmentsRegistry class attributes."""

    att = AttachmentsRegistry(id="id", name="name")

    att.id = "fake_id"
    assert att.fake_id == "You tried to access fake_id, but it doesn't exist!"
    assert att.id == "fake_id"
    assert format(att) == "id: fake_id name: name"


async def test_get_unread_messages():
    """Test the get_unread_messages method of the Komens class."""

    bakalari = Bakalari(server=fs, credentials=cred)
    komens = Komens(bakalari)

    with aioresponses() as m:
        m.post(
            url=fs + EndPoint.KOMENS_UNREAD.get("endpoint"),
            body=payload_unread,
            headers={},
            status=200,
        )

        msgs = await komens.get_unread_messages()
        assert isinstance(msgs, list)
        assert len(msgs) == 1
        assert msgs[0].isattachments() is True
        assert format(msgs[0]) == (
            "Message id: fake_id1\n"
            "title: \n"
            "text: fake_text_id1\n"
            "sent: 2024-01-01\n"
            "sender: fake_teacher_name1\n"
            "read: False\n"
            "attachments: id: fake_attachment_id1 name: fake_atachement_name1\n"
        )
        await bakalari.__aexit__()


async def test_komens_get_messages():
    """Test the Komens class and its methods."""

    bakalari = Bakalari(server=fs, credentials=cred)
    komens = Komens(bakalari)

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
            str(msgs) == "Message id: fake_id1\n"
            "title: \n"
            "text: fake_text_id1\n"
            "sent: 2024-01-01\n"
            "sender: fake_teacher_name1\n"
            "read: True\n"
            "attachments: id: fake_attachment_id1 name: fake_atachement_name1\n"
            "Message id: fake_id2\n"
            "title: \n"
            "text: fake_text_id2\n"
            "sent: 2024-01-05\n"
            "sender: fake_teacher_name2\n"
            "read: True\n"
            "attachments: \n"
        )
        assert_msgs = [
            {
                "mid": msg.mid,
                "title": msg.title,
                "text": msg.text,
                "sent": str(msg.sent),
                "sender": msg.sender,
                "read": msg.read,
                "attachments": msg.attachments_as_json(),
            }
            for msg in msgs
        ]

        assert msgs.json() == assert_msgs  # orjson.loads(orjson.dumps(assert_msgs))

        msg = komens.messages.get_messages_by_date(dt.date(2024, 1, 1))
        assert msg[0].mid == "fake_id1"

        msg = komens.messages.get_messages_by_date(
            dt.date(2024, 1, 1), to_date=dt.date(2024, 1, 1) + dt.timedelta(days=+5)
        )
        assert isinstance(msg, list)
        assert len(msg) == 2
        assert msg[1].mid == "fake_id2"
        assert (
            str(msg[1]) == "Message id: fake_id2\n"
            "title: \n"
            "text: fake_text_id2\n"
            "sent: 2024-01-05\n"
            "sender: fake_teacher_name2\n"
            "read: True\n"
            "attachments: \n"
        )

        assert (
            repr(msg[0])
            == "<MessageContainer message_id=fake_id1 title= sender=fake_teacher_name1 attachments=[<Attachments id=fake_attachment_id1 name=fake_atachement_name1>]>"
        )

        # JSON
        assert (
            msg[1].as_json()
            == b'{"mid":"fake_id2","title":"","text":"fake_text_id2","sent":"2024-01-05","sender":"fake_teacher_name2","read":true,"attachments":[]}'
        )

        msg[0].title = "new_set_title"
        assert msg[0].title == "new_set_title"

        # Test isattachments
        assert msg[0].isattachments() is True
        assert msg[1].isattachments() is False
        await bakalari.__aexit__()


async def test_komens_count_unread_messages():
    """Test the count_unread_messages method of the Komens class."""

    bakalari = Bakalari(server=fs, credentials=cred)
    komens = Komens(bakalari)

    with aioresponses() as m:
        m.get(
            url=fs + EndPoint.KOMENS_UNREAD_COUNT.get("endpoint"),
            body="50",
            headers={},
            status=200,
        )

        assert await komens.count_unread_messages() == 50
    await bakalari.__aexit__()

async def test_komens_get_attachment():
    """Test the get_attachment method of the Komens class."""

    bakalari = Bakalari(server=fs, credentials=cred)
    komens = Komens(bakalari)

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
    await bakalari.__aexit__()
