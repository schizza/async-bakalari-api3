from .bakalari import Bakalari
from .const import EndPoint


class Komens:
    """Class for manipulating Komens messages."""

    def __init__(self, bakalari: Bakalari):
        """Initialize class Komens."""
        self._bakalari = bakalari

    async def messages(self):
        """Get unread messages."""
        return await self._bakalari.send_auth_request(EndPoint.KOMENS_UNREAD)

    async def count_unread_messages(self):
        """Get count of unreaded messages."""
        return await self._bakalari.send_auth_request(
            EndPoint.KOMENS_UNREAD_COUNT)
