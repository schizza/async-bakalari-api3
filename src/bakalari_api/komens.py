"""Module for working with Komens."""

from datetime import datetime as dt
from typing import Any

import dateutil
import dateutil.parser
import orjson

from .bakalari import Bakalari
from .const import EndPoint
from .logger_api import api_logger

log = api_logger("Bakalari API").get()


class MessageContainer:
    """Messages registry."""

    mid: str
    title: str
    text: str
    sent: dt
    sender: dict[str, str]
    attachments: dict[str, str]

    def __init__(
        self,
        *,
        mid: str,
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
        _setter(self, "sent", sent.date())
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

    def as_json(self) -> bytes:
        """Return JSON fragment of message."""
        json_repr = {
            "mid": self.mid,
            "title": self.title,
            "text": self.text,
            "sent": self.sent,
            "sender": self.sender,
            "attachments": self.attachments,
        }
        return orjson.dumps(json_repr)

    def __str__(self) -> str:
        """Return string representation of data."""
        return f"""Message id: {self.mid}
            title: {self.title}
            text: {self.text}
            sent: {self.sent}
            sender: {self.sender}
            attachments: {self.attachments}"""


class Messages(list[MessageContainer]):
    """Messages class holds all messages."""

    def __init__(self) -> None:
        """Messages class holds all messages."""
        super().__init__()

    def __str__(self) -> str:
        """Print string representation."""

        text = ""
        for message in self:
            text += message.__str__() + "\n"
        return text

    def json(self):
        """Return json representation of Messages."""

        return [orjson.loads(m.as_json()) for m in self]

    def get_message_by_id(self, id: str) -> MessageContainer:
        """Get message by id."""
        for i in self:
            if i.mid == id:
                return i

    def get_messages_by_date(
        self, date: dt, to_date: dt | None = None
    ) -> list[MessageContainer]:
        """Get messages by date.

        If `to_date` is set, then returns list of range from `date` to `to_date`
        """

        to_date = to_date or date

        messages = [i for i in self if date <= i.sent <= to_date]

        return messages if messages else None

    def count_messages(self) -> int:
        """Count messages."""
        return len(self)


class Komens:
    """Class for working with Komens messages."""

    def __init__(self, bakalari: Bakalari):
        """Initialize class Komens."""
        self.bakalari = bakalari
        self.messages = Messages()

    async def fetch_messages(self) -> Messages:
        """Fetch unread messages.

        Retrieve messages from the server and returns an instance of the Messages class
        containing the messages.

        Returns:
            Messages: An instance of the Messages class containing the messages.

        """
        self.messages.clear()
        messages = await self.bakalari.send_auth_request(
            EndPoint.KOMENS_UNREAD,
        )

        async def create_msg(msg):
            log.debug(f"Writing message: {msg}")
            return MessageContainer(
                mid=msg["Id"],
                title=msg["Title"],
                text=msg["Text"],
                sent=dateutil.parser.parse(msg["SentDate"]),
                sender=msg["Sender"]["Name"],
                attachments=msg["Attachments"],
            )

        self.messages.extend([(await create_msg(msg)) for msg in messages["Messages"]])

        return self.messages

    async def count_unread_messages(self) -> int:
        """Get count of unreaded messages."""
        return await self.bakalari.send_auth_request(EndPoint.KOMENS_UNREAD_COUNT)

    async def get_attachment(self, id: str) -> Any:
        """Get attachment.

        Retrieves an attachment from the server based on the provided ID.

        Args:
            id (str): The ID of the attachment to retrieve.

        Returns:
            Tuple[str, Any]: A tuple containing the filename and file data of the attachment.

        """
        try:
            filename, filedata = await self.bakalari.send_auth_request(
                EndPoint.KOMENS_ATTACHMENT, extend=f"/{id}"
            )
        except Exception as ex:
            log.error(f"Exception: {ex} has occurred.")
            return False

        return filename, filedata
