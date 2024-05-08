"""Main module."""

import asyncio

import orjson

from .bakalari import Bakalari, Schools
from .komens import Komens
from .first_login import first_login


async def runme():

    schools: Schools = await Schools().load_from_file("schools_data.json")
    server = schools.get_url("Kadaňská")
    bakalari = Bakalari(
        server=server, auto_cache_credentials=True, cache_filename="new_data.json"
    )
    bakalari.load_credentials("new_data.json")

    try:
        komens = Komens(bakalari)
        unread_messages = await komens.count_unread_messages()
        print(unread_messages)
    except Exception as ex:
        print(ex)

    print("Main done.")


def main() -> None:

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runme())
