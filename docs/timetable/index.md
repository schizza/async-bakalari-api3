# Modul Timetable

Modul Timetable zajišťuje načtení a zpracování rozvrhu (aktuálního i stálého) ze serveru Bakalářů. Umí:

- stáhnout aktuální rozvrh pro zadané datum,
- stáhnout stálý (permanentní) rozvrh,
- vrátit rozparsovaná data do přehledných tříd,
- formátovat rozvrh do čitelného textu (den/týden).

Tento modul provádí autorizované dotazy. Před použitím tedy musíte mít platné přihlašovací údaje (tokeny) v instanci `Bakalari`. Viz [první přihlášení](../bakalari/first_login.md) a [Credentials](../bakalari/credentials.md).

---

## Třída Timetable

```py linenums="1" title="class Timetable"
from async_bakalari_api import Bakalari
from async_bakalari_api.timetable import Timetable

class Timetable:
    """Client for fetching and parsing timetable endpoints."""

    def __init__(self, bakalari: Bakalari) -> None: ...
```

!!! notice ""
    - Konstruktor přijímá pouze instanci `Bakalari`.
    - Modul využívá interně autorizované volání (`send_auth_request`) a tokeny si automaticky obnovuje.

### Použití s context managerem

```py linenums="1" title="Context manager"
from async_bakalari_api import Bakalari
from async_bakalari_api.timetable import Timetable

bakalari = Bakalari("https://server_skoly")
bakalari.load_credentials("credentials.json")

async with Timetable(bakalari) as tt:
    week = await tt.fetch_actual()  # aktuální týden
    print(week.format_week())
```

Context manager zajistí otevření/zavření HTTP session přes `Bakalari`.

---

## Filtrační kontext (TimetableContext)

Pro filtrování rozvrhu (třída, skupina, učitel, učebna, student) se používá `TimetableContext`. Ten se následně převádí na query parametry pro API.

```py linenums="1" title="TimetableContext"
from async_bakalari_api.timetable import TimetableContext

ctx = TimetableContext(kind="class", id="TRIDA_ID")        # classId=...
# ctx = TimetableContext(kind="group", id="SKUPINA_ID")    # groupId=...
# ctx = TimetableContext(kind="teacher", id="UCITEL_ID")   # teacherId=...
# ctx = TimetableContext(kind="room", id="MISTNOST_ID")    # roomId=...
# ctx = TimetableContext(kind="student", id="STUDENT_ID")  # studentId=...
```

Místo `TimetableContext` lze předat i přímo `dict` s parametry.

---

## Hlavní metody

### fetch_actual

```py linenums="1"
async def fetch_actual(
    self,
    for_date: datetime | date | None = None,
    context: TimetableContext | dict[str, str] | None = None,
) -> TimetableWeek: ...
```

- `for_date`: datum/datetime, pro které chcete načíst aktuální týden (výchozí: dnešní den). Do API se posílá jako `date=YYYY-MM-DD`.
- `context`: filtr rozvrhu (viz `TimetableContext` nebo dict s parametry).
- Návrat: `TimetableWeek` – rozparsovaný týden (viz níže).
- Vedlejší efekt: poslední načtený aktuální týden je uložen v `get_last_actual()`.

Příklad:

```py linenums="1"
from datetime import date
from async_bakalari_api.timetable import Timetable, TimetableContext

tt = Timetable(bakalari)
week = await tt.fetch_actual(for_date=date.today(),
                             context=TimetableContext(kind="class", id="1.A"))
print(week.format_week())
```

### fetch_permanent

```py linenums="1"
async def fetch_permanent(
    self,
    context: TimetableContext | dict[str, str] | None = None,
) -> TimetableWeek: ...
```

- `context`: filtr rozvrhu (volitelně).
- Návrat: `TimetableWeek`.
- Vedlejší efekt: poslední načtený stálý týden je uložen v `get_last_permanent()`.

Příklad:

```py linenums="1"
permanent = await tt.fetch_permanent(context={"classId": "1.A"})
print(permanent.format_week())
```

### get_last_actual / get_last_permanent

```py linenums="1"
last_actual: TimetableWeek | None = tt.get_last_actual()
last_perm: TimetableWeek | None = tt.get_last_permanent()
```

Vrátí poslední úspěšně načtený týden (nebo `None`).

---

## Datové struktury

### TimetableWeek

Kontejner s kompletními daty pro jeden týden:

```py linenums="1"
class TimetableWeek:
    hours: dict[int, Hour]
    days: list[DayEntry]
    classes: dict[str, ClassEntity]
    groups: dict[str, GroupEntity]
    subjects: dict[str, SubjectEntity]
    teachers: dict[str, TeacherEntity]
    rooms: dict[str, RoomEntity]
    cycles: dict[str, CycleEntity]

    def get_day_by_date(self, day: datetime | date) -> DayEntry | None: ...
    def get_day_by_weekday(self, weekday: int) -> DayEntry | None: ...
    def resolve(self, atom: Atom) -> tuple[SubjectEntity | None, TeacherEntity | None, RoomEntity | None, list[GroupEntity]]: ...
    def format_day(self, day: DayEntry) -> str: ...
    def format_week(self) -> str: ...
```

- `get_day_by_date(...)`: vrátí konkrétní den dle data.
- `get_day_by_weekday(weekday)`: vrátí den dle indexu dne z API (1=pondělí ... 7=neděle, pokud je k dispozici).
- `resolve(atom)`: namapuje ID v atomech na konkrétní entity (předmět, učitel, místnost, skupiny).
- `format_day(day)`: vrátí čitelný text pro jeden den.
- `format_week()`: vrátí čitelný text pro celý týden.

### Hour

Definice vyučovací hodiny:

```py linenums="1"
class Hour:
    id: int
    caption: str
    begin_time: str
    end_time: str
```

### DayEntry

Jeden den v týdnu:

```py linenums="1"
class DayEntry:
    day_of_week: int
    date: datetime
    description: str
    day_type: str
    atoms: list[Atom]
```

### Atom

Jednotka rozvrhu (hodina/blok), případně „placeholder“ se změnou:

```py linenums="1"
class Atom:
    hour_id: int
    group_ids: list[str]
    subject_id: str | None
    teacher_id: str | None
    room_id: str | None
    cycle_ids: list[str]
    change: Change | None
    homework_ids: list[str]
    theme: str | None
```

### Change

Změna v rozvrhu:

```py linenums="1"
class Change:
    change_subject: str | None
    day: datetime
    hours: str | None
    change_type: str | None
    description: str | None
    time: str | None
    type_abbrev: str | None
    type_name: str | None
```

### Entity

Základní entity s identifikátory (ID jsou ve slovnících uloženy jako `str`):

```py linenums="1"
class ClassEntity:   id: str; abbrev: str; name: str
class GroupEntity:   class_id: str | None; id: str; abbrev: str; name: str
class SubjectEntity: id: str; abbrev: str; name: str
class TeacherEntity: id: str; abbrev: str; name: str
class RoomEntity:    id: str; abbrev: str; name: str
class CycleEntity:   id: str; abbrev: str; name: str
```

---

## Příklady

### Aktuální týden pro třídu

```py linenums="1"
from async_bakalari_api import Bakalari
from async_bakalari_api.timetable import Timetable, TimetableContext

bakalari = Bakalari("https://server_skoly")
bakalari.load_credentials("credentials.json")

tt = Timetable(bakalari)
week = await tt.fetch_actual(context=TimetableContext(kind="class", id="1.A"))
print(week.format_week())
```

### Stálý rozvrh pro učitele

```py linenums="1"
teacher_week = await tt.fetch_permanent(context=TimetableContext(kind="teacher", id="TCHR_42"))
some_day = teacher_week.get_day_by_weekday(1)  # pondělí
if some_day:
    print(teacher_week.format_day(some_day))
```

### Ruční řešení vazeb a formátování

```py linenums="1"
# Vypsat první den a jeho hodiny se subjektem, učitelem a místností
first_day = week.days[0]
for atom in first_day.atoms:
    subj, teach, room, groups = week.resolve(atom)
    print(atom.hour_id,
          subj.abbrev if subj else "",
          teach.abbrev if teach else "",
          room.abbrev if room else "",
          ",".join(g.abbrev for g in groups))
```

---

## Poznámky a chování

- API vrací data v různých strukturách; parser v modulu se snaží být tolerantní.
  - Nevalidní položky se přeskočí a do logu se zapíše upozornění (warning).
  - ID se ukládají jako řetězce (ořezané o případné bílé znaky).
- Datum se do endpointu „aktuální rozvrh“ posílá jako `date=YYYY-MM-DD`.
- Metody `format_day`/`format_week` dokáží zobrazit:
  - číslo hodiny a čas,
  - předmět (zkratku),
  - skupiny,
  - učitele,
  - místnost,
  - téma (`theme`),
  - případně i záznam o změně (typ/čas/popis).
- Chyby autorizace a síťové chyby se propisují jako výjimky definované v balíčku (např. `Ex.AccessTokenExpired`, `Ex.RefreshTokenExpired`, `Ex.BadRequestException` aj.). Při expirovaném access tokenu se provede automatické obnovení přes refresh token a požadavek se zopakuje (max. jednou).
