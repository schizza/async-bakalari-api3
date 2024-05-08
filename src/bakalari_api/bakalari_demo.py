"""Main module."""

import asyncio

import orjson

from src.bakalari_api import Bakalari, Schools


SERVER = "https://kadanska.chomutov.cz"


# async def first_login(bak: Bakalari):
#     c = await bak.first_login("Svobo78361", "0DPmd0W8")


# async def komens_msg(bak: Bakalari):
#     try:
#         komens = await Komens(bak).messages_unread()

#     except Ex.TokensExpired as exc:
#         print(f"Access token expired! Use login to refresh tokens. Error: {exc}")
#         return
#     except Ex.AccessTokenExpired:
#         if bak.new_token:
#             print("Refreshing token.")
#             try:
#                 komens = await Komens(bak).messages_unread()
#             except Ex.TokensExpired as err:
#                 print(f"Error: {err}")
#                 return 0

#     with open("resp.json", "wb") as file:
#         file.write(orjson.dumps(komens, option=orjson.OPT_INDENT_2))
#         file.close()


async def runme():
    # schools = await Schools().load_from_file("schools_data.json")
    # bak = Bakalari(auto_cache_credentials=True, cache_filename="new_data.json")
    # if (schools):
    #     bak.server = schools.get_url(name="Kadaňská")
    # bak.load_credentials("new_data.json")

    # # await first_login(bak=bak)

    # print(
    #     f"Trying to get messages from {schools.get_school_name_by_api_point(bak.server)} at {bak.server}"
    # )
    # try:
    #     count = await Komens(bak).count_unread_messages()
    #     print(count)
    # except Ex.TokensExpired as err:
    #     print(f"Could not retrieve messages. {err}")

    schools: Schools = await Schools().load_from_file("schools_data.json")

    print(schools.get_schools_by_town("Chomutov"))

    print("Main done.")


def main() -> None:

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runme())
