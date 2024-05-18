"""Main module."""

import argparse
import asyncio

from logger import logging
import orjson

from .bakalari import Bakalari, Schools
from .komens import Komens
from .logger_api import api_logger


def w(name, data):
    """Write JSON data to file."""
    with open(name, "+wb") as fi:
        fi.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


def wb(name, data):
    """Write data to file."""
    with open(name, "wb") as fi:
        fi.write(data)


def r(name):
    """Read data from file."""
    with open(name, "rb") as fi:
        return orjson.loads(fi.read())


async def schools(args, bakalari: Bakalari):
    """Run school func.

    Args:
        args: The command line arguments.
        bakalari: An instance of the Bakalari class.

    """
    if args.schoollist and not args.town:
        schools: Schools = await bakalari.schools_list()
        for school in schools.school_list:
            print(f"Jméno školy: {school.name}")
            print(f"Město: {school.town}")
            print(f"api_point: {school.api_point}")
            print("-------------")

    elif args.schoollist and args.town:
        try:
            schools: Schools = await bakalari.schools_list(town=args.town)
            for school in schools.school_list:
                print(f"Jméno školy: {school.name}")
                print(f"Město: {school.town}")
                print(f"api_point: {school.api_point}")
                print("-------------")
        except Exception as ex:
            print(ex)
    elif args.schools_file:
        try:
            _schools: Schools = await bakalari.schools_list(town=args.town)
            w(args.schools_file, _schools.school_list)
        except Exception as ex:
            print(ex)


async def komens(args, bakalari):
    """Komens command."""
    if args.komens_list:
        print(await Komens(bakalari=bakalari).fetch_messages())
    if args.extend:
        messages = await Komens(bakalari=bakalari).fetch_messages()
        print(messages.get_message_by_id(args.extend))
    if args.komens_save:
        messages = await Komens(bakalari=bakalari).fetch_messages()
        w(args.komens_save, messages.json())
    if args.attachment:
        wb(*(await Komens(bakalari=bakalari).get_attachment(args.attachment)))


async def runme(args):
    """Run the main function."""

    if args.sf:
        schools: Schools = await Schools().load_from_file(args.sf)
    else:
        schools: Schools = await Bakalari().schools_list(town=args.town)

    school = args.school
    if school:
        server = schools.get_url(school)

    if args.no_login:
        bakalari = Bakalari()

    if args.first_login or args.first_login_file:

        cache = True if args.auto_cache else False

        bakalari = Bakalari(
            server=server, auto_cache_credentials=cache, cache_filename=args.auto_cache
        )

        if args.first_login_file:
            data = r(args.first_login_file[0])
            login = data["username"]
            passw = data["password"]
        else:
            login = args.first_login[0]
            passw = args.first_login[1]

        credentials = await bakalari.first_login(login, passw)

        if args.credentials_file:
            w(args.credentials_file, credentials)
        else:
            print(
                f"Access token: {credentials.access_token}\nRefresh token: {credentials.refresh_token}"
            )

        print(
            f"Cahce: {bakalari.auto_cache_credentials}  cache_filename={bakalari.cache_filename} server: {bakalari.server}"
        )
    if args.credentials:

        bakalari = Bakalari(server=server)
        credentials = r(args.credentials_file)
        bakalari.credentials.access_token = credentials["access_token"]
        bakalari.credentials.refresh_token = credentials["refresh_token"]

    if args.auto_cache:
        bakalari = Bakalari(
            server=server, auto_cache_credentials=True, cache_filename=args.auto_cache
        )
        bakalari.load_credentials(args.auto_cache)

    if "func" in args:
        await args.func(args, bakalari=bakalari)


def main() -> None:
    """Run DEMO func."""

    parser = argparse.ArgumentParser(description="Bakalari DEMO App", prog="bakalari")

    parser_login = parser.add_argument_group(
        "Přihlášení (požadováno)", "Zvolte typ přihlášení heslo / tokenu"
    )
    login_type = parser_login.add_mutually_exclusive_group(required=True)

    login_type.add_argument(
        "-N", "--no_login", action="store_true", help="Provede neautorizovaný přístup"
    )
    login_type.add_argument(
        "-F",
        "--first_login",
        nargs=2,
        metavar=("jméno", "heslo"),
        help="""Provede přihlášení jménem a heslem.
                Pokud je zadán parametr -cf, pak zapíše tokeny do tohoto souboru. Jinak tokeny zobrazí na výstup.
                Pokud je použit parametr --auto_cache, pak se tokeny zapíší do tohoto souboru i do souboru zadaného v parametru -cf.

                Škola může být pouze část názvu, ale název musí být jedinečný v seznamu škol.
                Pro rychlejší vyhledávání můžete přidat parametr -t k vyhledávání pouze ve zvoleném městě.""",
    )
    login_type.add_argument(
        "-Ff",
        "--first_login_file",
        metavar=("SOUBOR"),
        nargs=1,
        help="Přihlášení se jménem a heslem načtených ze souboru. Soubor s přihlašovacím jménem a heslem ve formátu JSON.",
    )

    login_type.add_argument(
        "-C",
        "--credentials",
        action="store_true",
        help="Přihlášení pomocí tokenu. Vyžaduje parametr -cf",
    )
    parser_login.add_argument(
        "-cf",
        "--credentials_file",
        nargs=None,
        metavar="soubor s tokeny",
        help="Jméno souboru odkud se maji načíst tokeny.",
    )

    login_type.add_argument(
        "--auto_cache",
        nargs=None,
        dest="auto_cache",
        metavar="soubor s tokeny",
        help="Použít automatické kešování tokenů. Povinný je parametr jméno souboru do kterého se má kešovat.",
    )

    subparser = parser.add_subparsers(title="Seznam příkazů", help="")

    school_list_parser = subparser.add_parser("schools", help="Seznam škol")
    komens_parser = subparser.add_parser("komens", help="Komens")
    action_school = school_list_parser.add_mutually_exclusive_group(required=True)
    action_school.add_argument(
        "-l",
        "--list",
        dest="schoollist",
        action="store_true",
        help="Vypíše seznam všech škol. S parameter -t vypíše školy ze zvoleného města.",
    )
    action_school.add_argument(
        "-s",
        "--save",
        nargs=None,
        metavar="Jméno souboru (formát JSON)",
        dest="schools_file",
        help="Uloží seznam škol do souboru.",
    )
    action_school.set_defaults(func=schools)

    parser.add_argument(
        "-t",
        "--town",
        nargs=None,
        metavar="Město",
        help="Omezí stahování a dotazy pouze na jedno město",
    )

    parser.add_argument(
        "-s",
        "--school",
        help="Název školy nebo část názvu školy",
        nargs=None,
        metavar="ŠKOLA",
    )

    parser.add_argument(
        "-sf",
        "--schools_file",
        dest="sf",
        nargs=None,
        metavar="SOUBOR.json",
        help="Načte seznam škol ze zadaného souboru (formát JSON)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Zapne podrobné logování"
    )

    komens_action = komens_parser.add_mutually_exclusive_group()
    komens_parser.add_argument(
        "--messages",
        action="store_true",
        help="Načte zprávy z Komens",
    )
    komens_action.add_argument(
        "-l",
        "--list",
        help="Vypíše přijaté zprávy",
        dest="komens_list",
        action="store_true",
    )
    komens_action.add_argument(
        "-e",
        "--extend",
        nargs=None,
        metavar="ID_zprávy",
        help="Vypíše podrobně zprávu s ID zprávy.",
    )
    komens_action.add_argument(
        "-s",
        "--save",
        help="Uloží zprávy do souboru",
        nargs=None,
        metavar="SOUBOR",
        dest="komens_save",
    )
    komens_action.set_defaults(func=komens)
    komens_parser.add_argument(
        "--attachment", nargs=None, metavar="ID_přílohy", help="Stáhne přílohu zprávy."
    )

    args = parser.parse_args()

    if args.verbose:
        api_logger("Bakalari API").get().setLevel(logging.DEBUG)

    asyncio.run(runme(args))
