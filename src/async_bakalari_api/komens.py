"""Module for working with Komens."""

from datetime import date, datetime
import logging
from typing import Any

import dateutil
import dateutil.parser
import orjson

from .bakalari import Bakalari
from .const import EndPoint

log = logging.getLogger(__name__)


class AttachmentsRegistry:
    """Attachments registry."""

    id: str
    name: str

    def __init__(self, *, id: str, name: str):
        """Initialize Attachments."""

        _setter = object.__setattr__
        _setter(self, "id", id)
        _setter(self, "name", name)

    def __setattr__(self, key: str, value: Any) -> None:
        """Set an attribute."""
        super().__setattr__(key, value)

    def __getattr__(self, key: str) -> Any:
        """Get an attribute."""
        log.error(f"AttributeError: {key} not found.")
        return f"You tried to access {key}, but it doesn't exist!"

    def __str__(self) -> str:
        """Return string representation of data."""
        return f"id: {self.id} name: {self.name}"

    def __repr__(self) -> str:
        """Representation of Attachments."""
        return f"<Attachments id={self.id} name={self.name}>"

    def __format__(self, format_spec: str) -> str:
        """Format string representation of data."""
        return self.__str__()

    def as_json(self) -> str:
        """Return JSON fragment of attachment."""

        return f"{{'id': {self.id}, 'name': {self.name}}}"


class MessageContainer:
    """Messages registry."""

    mid: str
    title: str
    text: str
    sent: datetime
    sender: dict[str, str]
    read: bool
    attachments: list[AttachmentsRegistry]

    def __init__(
        self,
        *,
        mid: str,
        title: str,
        text: str,
        sent: datetime,
        sender: dict[str, str],
        read: bool,
        attachments: list[AttachmentsRegistry] = [],
    ):
        """Initialize MessagesContainer."""

        if attachments != {}:
            attachments = [
                AttachmentsRegistry(id=i.get("Id"), name=i.get("Name"))
                for i in attachments
            ]

        _setter = object.__setattr__
        _setter(self, "mid", mid)
        _setter(self, "title", title)
        _setter(self, "text", text)
        _setter(self, "sent", sent.date())
        _setter(self, "sender", sender)
        _setter(self, "read", read)
        _setter(self, "attachments", attachments)

    def __repr__(self) -> str:
        """Representation of MessageContainer."""
        return (
            f"<MessageContainer message_id={self.mid} "
            f"title={self.title} sender={self.sender} "
            f"attachments={self.attachments}>"
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
            "read": self.read,
            "attachments": self.attachments_as_json(),
        }
        return orjson.dumps(json_repr)

    def __str__(self) -> str:
        """Return string representation of data."""
        att = (str(a) for a in self.attachments)
        return (
            f"Message id: {self.mid}\n"
            f"title: {self.title}\n"
            f"text: {self.text}\n"
            f"sent: {self.sent}\n"
            f"sender: {self.sender}\n"
            f"read: {self.read}\n"
            f"attachments: {''.join(att)}\n"
        )

    def __format__(self, format_spec: str) -> str:
        """Format string representation of data."""
        return self.__str__()

    def attachments_as_json(self) -> list[str]:
        """Return JSON fragment of attachments."""
        return [a.as_json() for a in self.attachments]

    def isattachments(self) -> bool:
        """Check if message contains attachment."""
        return bool(self.attachments)


class Messages(list[MessageContainer]):
    """Messages class holds all messages."""

    def __init__(self) -> None:
        """Messages class holds all messages."""
        super().__init__()

    def __str__(self) -> str:
        """Print string representation."""

        return "".join(str(message) for message in self)

    def json(self):
        """Return json representation of Messages."""

        return [orjson.loads(m.as_json()) for m in self]

    def get_message_by_id(self, id: str) -> MessageContainer:  # pyright: ignore[]
        """Get message by id."""
        for i in self:
            if i.mid == id:
                return i

    def get_messages_by_date(
        self, date: datetime | date, to_date: datetime | date | None = None
    ) -> list[MessageContainer]:
        """Get messages by date.

        If `to_date` is set, then returns list of range from `date` to `to_date`
        """

        if isinstance(date, datetime):
            date = date.date()

        if not to_date:
            to_date = date
        elif isinstance(to_date, datetime):
            to_date = to_date.date()

        if to_date < date:
            raise ValueError("to_date` must be after or equal to `date`")

        return [i for i in self if date <= i.sent <= to_date]

    def count_messages(self) -> int:
        """Count messages."""
        return len(self)


class Komens:
    """Class for working with Komens messages."""

    def __init__(self, bakalari: Bakalari):
        """Initialize class Komens."""
        self.bakalari = bakalari
        self.messages = Messages()
        self.noticeboard: Messages = Messages()

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

        self.messages.extend(
            [(await self.create_msg(msg)) for msg in messages["Messages"]]
        )

        return self.messages

    async def create_msg(self, msg):
        """Create a message containter from data."""
        log.debug(f"Writing message: {msg}")
        return MessageContainer(
            mid=msg["Id"],
            title=msg["Title"],
            text=msg["Text"],
            sent=dateutil.parser.parse(msg["SentDate"]),
            sender=msg["Sender"]["Name"],
            read=msg["Read"],
            attachments=msg["Attachments"],
        )

    async def fetch_noticeboard(self) -> Messages:
        """Fetch noticeboard messages."""

        "First clear messages"
        self.noticeboard.clear()

        noticeboard = await self.bakalari.send_auth_request(
            request_endpoint=EndPoint.NOTICEBOARD_ALL
        )
        noticeboard_object = Messages()

        noticeboard_object.extend(
            [(await self.create_msg(notice)) for notice in noticeboard["Messages"]]
        )

        self.noticeboard = noticeboard_object

        return noticeboard_object

    async def get_unread_messages(self) -> list[MessageContainer]:
        """Get unread messages."""
        if self.messages.count_messages() == 0:
            await self.fetch_messages()
        return [msg for msg in self.messages if msg.read is False]

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

    async def message_mark_read(self, id: str):
        """Mark message as read.

        Marks a message as read on the server.

        Args:
            id (str): The ID of the message to mark as read.

        """
        await self.bakalari.send_auth_request(
            EndPoint.KOMENS_MARK_READ, extend=f"/{id}/mark-as-read"
        )

    async def message_get_single_message(self, id: str) -> MessageContainer | None:
        """Get a single message.

        Retrieves a single message from the server based on the provided ID.

        Args:
            id (str): The ID of the message to retrieve.

        Returns:
            List[MessageContainer]: A list containing the retrieved message.

        """
        try:
            data = await self.bakalari.send_auth_request(
                EndPoint.KOMENS_GET_SINGLE_MESSAGE, extend=f"/{id}"
            )
            message = await self.create_msg(data.get("Message")[0])
        except Exception as ex:
            log.error(f"Exception: {ex} has occurred.")
            return None

        return message
