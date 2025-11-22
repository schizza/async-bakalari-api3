# async Bakaláři API v3

!!! warning "Upozornění"
    Toto API je stále vyvíjeno, a proto podporuje jen malé množství endpointů. Nicméně moduly zveřejněné v této dokumentaci jsou již stabilní.

`async Bakaláři API v3` je asynchronní klient pro komunikaci se školami, které jsou zapojeny do programu Bakaláři. Aplikace je napsána kompletně v Pythonu.

Má taktéž zabudovaný [modul pro příkazovou řádku](cli/index.md) `CLI` k jednoduchému použití.

Seznam všech škol zapojených do programu Bakaláři lze získat též z [tohoto modulu](bakalari/seznam_skol.md).

## Přehled modulů

- [Bakalari – základní klient](bakalari/index.md)
- [Komens – zprávy (příchozí, přílohy)](komens/index.md)
- [Marks – známky a statistiky](marks/index.md)
- [Timetable – rozvrh (aktuální i stálý)](timetable/index.md)

## Instalace

Modul lze nainstalovat jako balíček z [PyPI](https://pypi.org/project/async-bakalari-api/) nebo stáhnout z GitHubu.

!!! note ""
    Minimální verze Pythonu pro tento balíček je 3.12

=== ":simple-pypi: PyPI"

    ```shell
    python3 -m pip install async_bakalari_api
    ```

=== ":octicons-mark-github-16: GitHub"

    ```
    python3 -m pip install "git+https://github.com/schizza/async-bakalari-api3.git#egg=async-bakalari-api"
    ```
!!! tip "CLI"
    Po instalaci balíčku je dostupné jednoduché [CLI - `bakalari`](./cli/index.md)

## Praktický průvodce (workflow)

- Krok 1: Získání seznamu škol
  ```py
  from async_bakalari_api import Bakalari
  from async_bakalari_api.datastructure import Schools

  # Načtení ze serveru (doporučeno omezit městem a výsledek uložit)
  bakalari = Bakalari()
  schools = await bakalari.schools_list(town="Praha", recursive=False)
  if schools:
      await schools.save_to_file("schools.json")

  # nebo načtení ze souboru
  schools = await Schools().load_from_file("schools.json")
  server = schools.get_url("Část názvu školy")
  ```

- Krok 2: Přihlášení a tokeny
  ```py
  from async_bakalari_api import Bakalari

  # První přihlášení a automatické ukládání tokenů
  bakalari = Bakalari(server=server, auto_cache_credentials=True, cache_filename="credentials.json")
  async with bakalari:
      await bakalari.first_login("USERNAME", "PASSWORD")

  # Další běhy s automatickým načtením tokenů
  bakalari = Bakalari(server=server, auto_cache_credentials=True, cache_filename="credentials.json")
  bakalari.load_credentials("credentials.json")
  async with bakalari:
      # autorizované volání...
      pass
  ```

- Krok 3: Použití modulů
  - Komens (zprávy)
    ```py
    from async_bakalari_api.komens import Komens

    komens = Komens(bakalari)
    messages = await komens.fetch_messages()
    unread = await komens.get_unread_messages()
    ```
  - Marks (známky)
    ```py
    from async_bakalari_api.marks import Marks

    marks = Marks(bakalari)
    await marks.fetch_marks()
    summary = await marks.get_all_marks_summary()
    ```
  - Timetable (rozvrh)
    ```py
    from async_bakalari_api.timetable import Timetable, TimetableContext

    tt = Timetable(bakalari)
    week = await tt.fetch_actual(context=TimetableContext(kind="class", id="1.A"))
    print(week.format_week())
    ```

## Logování

Knihovna poskytuje jednoduchou konfiguraci logování s rozšířenými poli (event, url, method, latency_ms, retries, status, error).

```py
from async_bakalari_api import configure_logging
import logging

# Podrobné logy
configure_logging(logging.DEBUG)

# nebo pouze chyby
configure_logging(logging.ERROR)
```

- Alternativně lze úroveň řídit proměnnou prostředí:
  - BAKALARI_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
- Logy jsou strukturované a barevné (pro snazší čtení v terminálu).

## Výjimky (Exceptions)

Běžné doménové chyby vystavuje jmenný prostor `Ex`:

- Ex.InvalidLogin – neplatné přihlašovací údaje
- Ex.AccessTokenExpired – vypršel access token (proběhne auto-refresh)
- Ex.RefreshTokenExpired – vypršel/není platný refresh token (vyžaduje znovu first_login)
- Ex.InvalidToken – neplatný token
- Ex.InvalidRefreshToken – neplatný refresh token
- Ex.RefreshTokenRedeemd – refresh token byl již uplatněn
- Ex.TokenMissing – chybí access/refresh token
- Ex.BadRequestException – obecná chyba požadavku (4xx/5xx, nesprávné parametry apod.)
- Ex.InvalidHTTPMethod – endpoint nepodporuje metodu
- Ex.TimeoutException – vypršel timeout požadavku
- Ex.BadEndpointUrl – špatně složená URL (např. chybějící server)
- Ex.InvalidCredentials, Ex.InvalidResponse, Ex.TokensExpired, Ex.CacheError – ostatní stavy

Ukázka ošetření chyb při volání API:
```py
from async_bakalari_api import Bakalari
from async_bakalari_api.const import EndPoint
from async_bakalari_api.exceptions import Ex

bakalari = Bakalari(server="https://server_skoly")

try:
    async with bakalari:
        resp = await bakalari.send_auth_request(EndPoint.MARKS)
except Ex.AccessTokenExpired:
    # Obvykle se provede automatický refresh, sem se dostanete, pokud obnovu nelze provést.
    await bakalari.refresh_access_token()
except Ex.RefreshTokenExpired:
    # Nelze obnovit – je nutné přihlášení jménem a heslem
    await bakalari.first_login("USERNAME", "PASSWORD")
except Ex.BadRequestException as e:
    print(f"Chybný požadavek: {e}")
```
