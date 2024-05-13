"""Main module."""

import asyncio

import orjson

from .bakalari import Bakalari, Schools
from .komens import Komens, Messages, MessageContainer
from .first_login import first_login

import datetime


def w(data):
    with open(".data", "+wb") as fi:
        fi.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        fi.close()


async def runme():

    # await first_login()

    schools: Schools = await Schools().load_from_file("schools_data.json")
    server = schools.get_url("Kadaňská")

    bakalari = Bakalari(
        server=server, auto_cache_credentials=True, cache_filename="new_data.json"
    )
    bakalari.load_credentials("new_data.json")
    k = Komens(bakalari=bakalari)

    await k.get_messages()
    print(k.messages.count_messages())

    print(datetime.date.today() + datetime.timedelta(days=-8))

    messages = k.messages.get_messages_by_date(
            datetime.date.today() + datetime.timedelta(days=-30),
            to_date=datetime.date.today(),
        )


    print(await k.count_unread_messages())
    
    for msg in messages:
        print(msg.text)


def main() -> None:

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runme())
