"""Main module."""

import argparse
import asyncio
from datetime import datetime
import logging
import sys

import aiofiles
import orjson

from .bakalari import Bakalari
from .datastructure import Credentials, Schools
from .komens import Komens, MessageContainer
from .logger_api import configure_logging
from .marks import Marks
from .timetable import Timetable, TimetableContext

log = logging.getLogger(__name__)


async def w(name, data):
    """Write JSON data to file."""
    async with aiofiles.open(name, "+wb") as fi:
        await fi.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        await fi.flush()
        log.debug(f"File {name} written")


async def wb(name, data):
    """Write data to file."""
    async with aiofiles.open(name, "wb") as fi:
        await fi.write(data)
        await fi.flush()
    log.debug(f"File {name} written")


def r(name):
    """Read data from file."""
    with open(name, "rb") as fi:
        return orjson.loads(fi.read())


async def schools(args, bakalari: Bakalari):  # noqa: C901
    """Run school func.

    Args:
        args: The command line arguments.
        bakalari: An instance of the Bakalari class.

    """
    if args.schoollist and not args.town:
        schools_res = await bakalari.schools_list(
            recursive=getattr(args, "recursive", True)
        )
        if not schools_res:
            print("Nepodařilo se načíst seznam škol.")
            return
        for school in schools_res.school_list:
            print(f"Jméno školy: {school.name}")
            print(f"Město: {school.town}")
            print(f"api_point: {school.api_point}")
            print("-------------")

    elif args.schoollist and args.town:
        try:
            schools_res = await bakalari.schools_list(
                town=args.town, recursive=getattr(args, "recursive", True)
            )
            if not schools_res:
                print("Nepodařilo se načíst seznam škol.")
                return
            for school in schools_res.school_list:
                print(f"Jméno školy: {school.name}")
                print(f"Město: {school.town}")
                print(f"api_point: {school.api_point}")
                print("-------------")
        except Exception as ex:
            print(ex)
    elif args.schools_file:
        try:
            _schools = await bakalari.schools_list(
                town=args.town, recursive=getattr(args, "recursive", True)
            )
            if not _schools:
                print("Nepodařilo se načíst seznam škol.")
                return
            await w(args.schools_file, _schools.school_list)
        except Exception as ex:
            print(ex)


async def komens(args, bakalari):  # noqa: C901
    """Komens command."""

    async def create_attachment_task(message: MessageContainer):
        """Create a task for saving an attachment."""
        tasks = []
        if args.komens_save_attachment:
            if message.isattachments():
                for att in message.attachments:
                    task = asyncio.create_task(
                        wb(*(await Komens(bakalari=bakalari).get_attachment(att.id)))
                    )
                    tasks.append(task)
        return tasks

    async def msgs(messages):
        """Print messages and save attachments if needed."""
        tasks = []
        for msg in messages:
            print(str(msg))
            tasks = await create_attachment_task(msg)

        await asyncio.gather(*tasks)

    async def msgs_w(messages):
        """Save messages and attachments if needed."""
        tasks = []

        if isinstance(messages, MessageContainer):
            await wb(args.komens_save, messages.as_json())
            tasks.extend(await create_attachment_task(messages))

        if isinstance(messages, list):
            for msg in messages:
                await wb(f"{args.komens_save}_{msg.mid}.json", msg.as_json())
                tasks.extend(await create_attachment_task(msg))

        await asyncio.gather(*tasks)

    if args.komens_list:
        if not args.komens_unread:
            await msgs(await Komens(bakalari=bakalari).fetch_messages())
        else:
            await msgs(await Komens(bakalari=bakalari).get_unread_messages())

    if args.extend:
        messages = await Komens(bakalari=bakalari).fetch_messages()
        await msgs([messages.get_message_by_id(args.extend)])

    if args.komens_save:
        if not args.komens_unread:
            await msgs_w(await Komens(bakalari=bakalari).fetch_messages())
        else:
            await msgs_w(await Komens(bakalari=bakalari).get_unread_messages())

    if args.attachment:
        await wb(*(await Komens(bakalari=bakalari).get_attachment(args.attachment)))


async def marks(args, bakalari):  # noqa: C901
    """Mark command."""
    # Local import to avoid touching global imports block

    # Parse filters
    date_from = None
    date_to = None
    if getattr(args, "marks_from", None):
        try:
            date_from = datetime.fromisoformat(args.marks_from)
        except Exception as ex:
            print(
                f"Neplatný formát data pro --from: {args.marks_from} (YYYY-MM-DD) — {ex}"
            )
            return
    if getattr(args, "marks_to", None):
        try:
            date_to = datetime.fromisoformat(args.marks_to)
        except Exception as ex:
            print(f"Neplatný formát data pro --to: {args.marks_to} (YYYY-MM-DD) — {ex}")
            return
    subject_id = getattr(args, "marks_subject", None)

    m = Marks(bakalari=bakalari)
    await m.fetch_marks()

    # subjects list
    if getattr(args, "marks_subjects", False):
        subs = await m.get_subjects()
        for s in subs:
            print(f"{s.id}\t{s.abbr}\t{s.name}")
        return

    # summary
    if getattr(args, "marks_summary", False):
        summary = await m.get_all_marks_summary()
        print(orjson.dumps(summary, option=orjson.OPT_INDENT_2).decode())
        return

    # snapshot save
    if getattr(args, "marks_save", None):
        # If only new or unconfirmed requested, use predicate
        predicate = None
        if getattr(args, "marks_new", False):

            def _predicate_new(it):
                return it.is_new

            predicate = _predicate_new
        elif getattr(args, "marks_unconfirmed", False):

            def _predicate_unconfirmed(it):
                return not it.confirmed

            predicate = _predicate_unconfirmed
        snapshot = await m.get_snapshot(
            date_from=date_from,
            date_to=date_to,
            subject_id=subject_id,
            order="desc",
            predicate=predicate,
            to_dict=True,
        )
        await wb(args.marks_save, orjson.dumps(snapshot, option=orjson.OPT_INDENT_2))
        print(f"Uloženo: {args.marks_save}")
        return

    # list/print
    if getattr(args, "marks_list", False):
        # With filters and possible predicate, print custom format
        predicate = None
        if getattr(args, "marks_new", False):

            def _predicate_new(it):
                return it.is_new

            predicate = _predicate_new
        elif getattr(args, "marks_unconfirmed", False):

            def _predicate_unconfirmed(it):
                return not it.confirmed

            predicate = _predicate_unconfirmed
        if predicate:
            for subj, marks in m.iter_grouped(
                date_from=date_from,
                date_to=date_to,
                subject_id=subject_id,
                predicate=predicate,
            ):
                header = f"{subj.name} ({subj.abbr}) | average: {subj.average_text} | points_only: {subj.points_only}"
                print(header)
                print("-" * len(header))
                for mk in marks:
                    mark_text = mk.marktext.text if mk.marktext else ""
                    caption = mk.caption or ""
                    line = f"  [{mk.date.date()}] {caption} -> {mark_text}"
                    if mk.is_new:
                        line += " [NEW]"
                    if not mk.confirmed:
                        line += " [UNCONFIRMED]"
                    print(line)
                    if mk.theme:
                        print(f"    theme: {mk.theme.strip()}")
                    if mk.is_points:
                        pt = mk.points_text or ""
                        if mk.max_points is not None:
                            print(f"    points: {pt} / {mk.max_points}")
                        else:
                            print(f"    points: {pt}")
                print("")
        else:
            text = await m.format_all_marks(
                date_from=date_from, date_to=date_to, subject_id=subject_id
            )
            print(text)
        return


async def request_custom(args, bakalari):  # noqa: C901
    """Request custom command."""
    url = args.req_endpoint
    if not (url.lower().startswith("http://") or url.lower().startswith("https://")):
        if not bakalari.server:
            print("Není zadán server ani plná URL endpointu.")
            return
        url = f"{bakalari.server}{url}"

    method = (args.req_method or "GET").upper()
    headers: dict[str, str] = {}
    data_kwargs = {}

    if getattr(args, "req_json", None):
        try:
            payload = orjson.loads(args.req_json)
        except Exception as ex:
            print(f"Neplatný JSON v --json: {ex}")
            return
        headers["Content-Type"] = "application/json"
        data_kwargs["json"] = payload
    elif getattr(args, "req_data", None):
        data_kwargs["data"] = args.req_data

    try:
        result = await bakalari._api_client.authorized_request(
            url,
            method=method,
            credentials=bakalari.credentials,
            refresh_callback=bakalari.refresh_access_token,
            headers=headers,
            **data_kwargs,
        )
    except Exception as ex:
        print(f"Chyba požadavku: {ex}")
        return

    if isinstance(result, (dict, list)):
        print(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode())
    elif isinstance(result, (str, bytes)):
        if isinstance(result, bytes):
            try:
                print(result.decode())
            except Exception:
                print(str(result))
        else:
            print(result)
    elif result is None:
        print("Bez obsahu (204 No Content)")
    else:
        print(str(result))


async def timetable(args, bakalari):
    """Timetable command."""
    # Build context if provided
    ctx = None
    if getattr(args, "tt_class", None):
        ctx = TimetableContext("class", args.tt_class)
    elif getattr(args, "tt_group", None):
        ctx = TimetableContext("group", args.tt_group)
    elif getattr(args, "tt_teacher", None):
        ctx = TimetableContext("teacher", args.tt_teacher)
    elif getattr(args, "tt_room", None):
        ctx = TimetableContext("room", args.tt_room)
    elif getattr(args, "tt_student", None):
        ctx = TimetableContext("student", args.tt_student)

    # Parse date if provided
    date_val = None
    if getattr(args, "tt_date", None):
        try:
            date_val = datetime.fromisoformat(args.tt_date).date()
        except Exception as ex:
            print(f"Neplatný formát data: {args.tt_date} (očekáváno YYYY-MM-DD) — {ex}")
            return

    tt = Timetable(bakalari=bakalari)
    if getattr(args, "tt_permanent", False):
        week = await tt.fetch_permanent(context=ctx)
    else:
        week = await tt.fetch_actual(for_date=date_val, context=ctx)

    print(week.format_week())


async def runme(args):  # noqa: C901
    """Run the main function."""
    server = None
    schools_data = None
    bakalari = Bakalari()

    if args.config and not args.first_login and not args.first_login_file:
        try:
            async with aiofiles.open("config.json", "rb") as fi:
                data = await fi.read()
                try:
                    data = orjson.loads(data)
                except Exception as ex:
                    print(f"Neplatný konfigurační soubor. ({ex})")
                    sys.exit(1)
                server = data["school"]
                args.auto_cache = "credentials.json"
        except FileNotFoundError:
            print("Konfigurační soubor nenalezen.")
            sys.exit(1)

    if args.sf and not server:
        try:
            schools_data = await Schools().load_from_file(args.sf)
        except Exception:
            sys.exit(1)

    school = args.school
    if school and not server:
        if not schools_data:
            async with Bakalari() as _bak:
                schools_res = await _bak.schools_list(
                    town=args.town, recursive=getattr(args, "recursive", True)
                )
            if not schools_res:
                print("Nepodařilo se načíst seznam škol.")
                return
            schools_data = schools_res
        if isinstance(schools_data, Schools):
            server_candidate = schools_data.get_url(school)
        if not isinstance(server_candidate, str):
            print("Škola nebyla nalezena nebo není jednoznačná.")
            return
        server = server_candidate

    if args.no_login:
        bakalari = Bakalari()

    if args.first_login or args.first_login_file:
        cache = bool(args.auto_cache)

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

        async with bakalari:
            credentials = await bakalari.first_login(login, passw)

        if args.credentials_file and not args.config:
            await w(args.credentials_file, credentials)
        elif not args.config and not cache:
            print(
                f"Access token: {credentials.access_token}\nRefresh token: {credentials.refresh_token}"
            )
        if args.config:
            await w("config.json", {"school": server})
            await w("credentials.json", credentials)
        if cache:
            bakalari.save_credentials()

        print(
            f"Cahce: {bakalari.auto_cache_credentials}  cache_filename={bakalari.cache_filename} server: {bakalari.server}"
        )
    if args.credentials:
        cred = r(name=args.credentials_file)
        bakalari = Bakalari(
            server=server,
            credentials=Credentials(
                access_token=cred["access_token"], refresh_token=cred["refresh_token"]
            ),
        )

    if args.auto_cache and not (
        args.first_login or args.first_login_file or args.credentials
    ):
        bakalari = Bakalari(
            server=server, auto_cache_credentials=True, cache_filename=args.auto_cache
        )
        bakalari.load_credentials(args.auto_cache)

    if hasattr(args, "func"):
        async with bakalari:
            await args.func(args, bakalari=bakalari)


def main() -> None:
    """Run DEMO func."""

    parser = argparse.ArgumentParser(description="Bakalari DEMO App", prog="bakalari")

    parser_login = parser.add_argument_group(
        "Přihlášení (požadováno)", "Zvolte typ přihlášení heslo / tokenu"
    )
    login_type = parser_login.add_mutually_exclusive_group()

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

    parser_login.add_argument(
        "-a",
        "--auto",
        help="Při úspěšném přihlášení jménem a heslem uloží tokeny a název školy do konfiguračních souborů a později je použije k automatickému přihlášení.",
        action="store_true",
        dest="config",
    )
    parser_login.add_argument(
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

    # Globální volby rekurzivního (podřetězcového) filtrování názvu města/školy
    parser.add_argument(
        "-r--recursive",
        dest="recursive",
        action="store_true",
        default=True,
        help="Povolí rekurzivní (podřetězcové) vyhledávání (výchozí).",
    )
    parser.add_argument(
        "-nr",
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Zakáže rekurzivní vyhledávání (použije se pouze prefix).",
    )

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
        "-u",
        "--unread",
        help="Vypíše nepřečtené zprávy",
        dest="komens_unread",
        action="store_true",
    )
    komens_parser.add_argument(
        "-sa",
        "--save_attachment",
        action="store_true",
        help="Uloží automaticky přílohy zpráv do souboru",
        dest="komens_save_attachment",
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

    # Marks command
    marks_parser = subparser.add_parser("marks", help="Známky (marks)")
    marks_action = marks_parser.add_mutually_exclusive_group(required=True)
    marks_action.add_argument(
        "-l",
        "--list",
        dest="marks_list",
        action="store_true",
        help="Vypíše známky (volitelně filtrování dle data/předmětu).",
    )
    marks_action.add_argument(
        "-s",
        "--save",
        dest="marks_save",
        metavar="SOUBOR.json",
        help="Uloží snapshot známek do souboru (JSON).",
    )
    marks_action.add_argument(
        "--summary",
        dest="marks_summary",
        action="store_true",
        help="Vypíše souhrn známek (průměry, počty).",
    )
    marks_parser.add_argument(
        "--from",
        dest="marks_from",
        metavar="YYYY-MM-DD",
        help="Začátek intervalu (včetně) ve formátu YYYY-MM-DD.",
    )
    marks_parser.add_argument(
        "--to",
        dest="marks_to",
        metavar="YYYY-MM-DD",
        help="Konec intervalu (včetně) ve formátu YYYY-MM-DD.",
    )
    marks_parser.add_argument(
        "--subject",
        dest="marks_subject",
        metavar="SUBJECT_ID",
        help="Filtrování podle ID předmětu.",
    )
    marks_parser.add_argument(
        "--subjects",
        dest="marks_subjects",
        action="store_true",
        help="Vypíše seznam předmětů (ID, zkratka, název) pro filtrování.",
    )
    marks_parser.add_argument(
        "-n",
        "--new",
        dest="marks_new",
        action="store_true",
        help="Pouze nové známky.",
    )
    marks_parser.add_argument(
        "-u",
        "--unconfirmed",
        dest="marks_unconfirmed",
        action="store_true",
        help="Pouze nepotvrzené známky.",
    )
    marks_parser.set_defaults(func=marks)

    # Timetable command
    # Custom request command
    request_parser = subparser.add_parser("request", help="Vlastní request")
    request_parser.add_argument(
        "req_endpoint",
        metavar="ENDPOINT",
        help="Absolutní URL nebo relativní cesta (doplní se server).",
    )
    request_parser.add_argument(
        "-X",
        "--method",
        dest="req_method",
        choices=["GET", "POST", "PUT", "get", "post", "put"],
        default="GET",
        help="HTTP metoda (GET, POST, PUT).",
    )
    data_group = request_parser.add_mutually_exclusive_group()
    data_group.add_argument(
        "-d",
        "--data",
        dest="req_data",
        help="Tělo požadavku jako prostý řetězec (odesláno jako data).",
    )
    data_group.add_argument(
        "--json",
        dest="req_json",
        help="Tělo požadavku jako JSON řetězec.",
    )
    request_parser.set_defaults(func=request_custom)

    # Timetable command
    timetable_parser = subparser.add_parser("timetable", help="Rozvrh (timetable)")
    timetable_parser.add_argument(
        "-p",
        "--permanent",
        dest="tt_permanent",
        action="store_true",
        help="Načte pevný (permanentní) rozvrh místo aktuálního.",
    )
    timetable_parser.add_argument(
        "-d",
        "--date",
        dest="tt_date",
        metavar="YYYY-MM-DD",
        help="Datum týdne pro aktuální rozvrh ve formátu YYYY-MM-DD. Pokud není zadáno, použije se dnešní datum.",
    )
    tt_ctx = timetable_parser.add_mutually_exclusive_group()
    tt_ctx.add_argument(
        "--class",
        dest="tt_class",
        metavar="ID",
        help="ID třídy (classId) pro zobrazení rozvrhu.",
    )
    tt_ctx.add_argument(
        "--group",
        dest="tt_group",
        metavar="ID",
        help="ID skupiny (groupId) pro zobrazení rozvrhu.",
    )
    tt_ctx.add_argument(
        "--teacher",
        dest="tt_teacher",
        metavar="ID",
        help="ID učitele (teacherId) pro zobrazení rozvrhu.",
    )
    tt_ctx.add_argument(
        "--room",
        dest="tt_room",
        metavar="ID",
        help="ID místnosti (roomId) pro zobrazení rozvrhu.",
    )
    tt_ctx.add_argument(
        "--student",
        dest="tt_student",
        metavar="ID",
        help="ID studenta (studentId) pro zobrazení rozvrhu.",
    )
    timetable_parser.set_defaults(func=timetable)

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.verbose:
        configure_logging(logging.DEBUG)
    else:
        configure_logging(logging.ERROR)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runme(args))
