"""Module for working with Komens."""

from datetime import datetime as dt
from typing import Any

import dateutil
import orjson

from .bakalari import Bakalari
from .const import EndPoint
from .logger_api import api_logger

log = api_logger("Bakalari API").get()


class MessageContainer:
    """Messages registry."""

    mid: int
    title: str
    text: str
    sent: dt.date
    sender: dict[str, str]
    attachments: dict[str, str]

    def __init__(
        self,
        *,
        mid: int,
        title: str,
        text: str,
        sent: dt,
        sender: dict[str, str],
        attachments: dict[str, str] | None = None,
    ):
        """Initialize MessagesContainer."""

        _setter = object.__setattr__
        _setter(self, "mid", mid)
        _setter(self, "title", title)
        _setter(self, "text", text)
        _setter(self, "sent", sent)
        _setter(self, "sender", sender)
        _setter(self, "attachments", attachments)

    def __repr__(self) -> str:
        """Representation of MessageContainer."""
        return (
            f"<MessageContainer message_id={self.mid} "
            f"title={self.title} sender={self.sender}>"
        )

    def __setattr__(self, key: str, value: Any) -> None:
        """Set an attribute."""
        super().__setattr__(key, value)

    def as_json(self) -> orjson.Fragment:
        """Return JSON fragment of message."""
        json_repr = {
            "mid": self.mid,
            "title": self.title,
            "text": self.text,
            "sent": self.sent,
            "sender": self.sender,
            "attachments": self.attachments,
        }
        return orjson.Fragment(json_repr)

    def __str__(self) -> str:
        """Return string representation of data."""
        return f"""Message id: {self.mid}
            title: {self.title}
            text: {self.text},
            sent: {self.sent.date()},
            sender: {self.sender},
            attachments: {self.attachments}"""


class Messages(list[MessageContainer]):
    """Messages class holds all messages."""

    def __init__(self) -> None:
        """Messages class holds all messages."""
        super().__init__()

    def add_message(self, data: MessageContainer):
        """Add new message to list."""
        self.append([data])

    def get_message_by_id(self, id: int) -> MessageContainer:
        """Get message by id."""
        for i in self:
            if i[0].mid == id:
                return i[0]

    def get_messages_by_date(
        self, date: dt, to_date: dt | None = None
    ) -> list[MessageContainer]:
        """Get messages by date.

        If `to_date` is set, then returns list of range from `date` to `to_date`
        """

        messages = []

        for i in self:
            if to_date:
                if (i[0].sent.date() >= date) and (i[0].sent.date() <= to_date):
                    messages.append(i[0])
            elif i[0].sent.date() == date:
                messages.append(i[0])
        return None if len(messages) == 0 else messages

    def count_messages(self) -> int:
        """Count messages."""
        return len(self)


class Komens:
    """Class for working with Komens messages."""

    def __init__(self, bakalari: Bakalari):
        """Initialize class Komens."""
        self.bakalari = bakalari
        self.messages = Messages()

    async def get_messages(self) -> Messages:
        """Get unread messages."""
        messages = await self.bakalari.send_auth_request(
            EndPoint.KOMENS_UNREAD,
        )

        _messages = Messages()

        # with open(".data", "rb") as f:
        #     messages = orjson.loads(f.read())
        #     f.close()

        for msg in messages["Messages"]:
            log.debug(f"Writing message: {msg}")
            _message = MessageContainer(
                mid=msg["Id"],
                title=msg["Title"],
                text=msg["Text"],
                sent=dateutil.parser.parse(msg["SentDate"]),
                sender=msg["Sender"]["Name"],
                attachments=msg["Attachments"],
            )
            self.messages.add_message(_message)

        return _messages

    async def count_unread_messages(self) -> int:
        """Get count of unreaded messages."""
        return await self.bakalari.send_auth_request(EndPoint.KOMENS_UNREAD_COUNT)
