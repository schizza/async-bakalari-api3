# modul Bakalari

### Autorizované požadavky (send_auth_request)

``` py
async def send_auth_request(self, request_endpoint: EndPoint, extend: str | None = None, **kwargs) -> Any:
```

- Parametry:
  - `request_endpoint (EndPoint)`: cílový endpoint. HTTP metoda se odvozuje z definice endpointu (`get`/`post`).
  - `extend (str | None)`: volitelný přílepek na konec URL (např. `"/{id}"` pro stažení přílohy).
  - `**kwargs`: volitelné argumenty pro HTTP požadavek (např. `params=...`, `data=...`, `json=...`).

- Chování:
  - Provede autorizovaný požadavek s využitím `access_token`. Pokud je token neplatný/expiruje, proběhne automatický refresh přes `refresh_access_token()` a požadavek se zopakuje (1 pokus).
  - Hlavička `Authorization: Bearer <access_token>` je nastavena automaticky.
  - Návratová hodnota je surová odpověď serveru:
    - běžně JSON (dict/list),
    - pro binární soubory (např. příloha v Komens) dvojice `[filename, filedata]`.

- Výjimky:
  - `Ex.TokenMissing` (chybí přístupové tokeny),
  - `Ex.AccessTokenExpired`, `Ex.InvalidToken` (neplatný/expirující přístupový token),
  - `Ex.RefreshTokenExpired` (není možné obnovit token),
  - `Ex.BadRequestException` (ostatní chyby HTTP, 4xx/5xx),
  - případně specifické chyby dle `error_uri` vrácené serverem.

- Poznámka:
  - Pokud endpoint není absolutní URL, je složen ze `server` + `endpoint`. Metoda využívá vnitřní klient s jednotným logováním a měřením latencí.

---

### Neautorizované požadavky (send_unauth_request)

``` py
async def send_unauth_request(self, request: EndPoint, headers: dict[str, str] | None = None, **kwargs) -> Any:
```

- Parametry:
  - `request (EndPoint)`: cílový endpoint.
  - `headers (dict[str, str] | None)`: volitelné HTTP hlavičky; pokud nejsou zadány, použije se prázdný slovník.
  - `**kwargs`: volitelné argumenty pro HTTP požadavek (např. `params=...`, `data=...`, `json=...`).

- Chování:
  - Metoda zvolí HTTP metodu podle endpointu (`get` → GET, jinak POST).
  - Pro neautorizované volání (např. přihlášení nebo veřejné služby) – nepřidává hlavičku `Authorization`.
  - Návratová hodnota je surová odpověď serveru (typicky JSON). Pro binární odpovědi vrací `[filename, filedata]`.

- Výjimky:
  - `Ex.InvalidLogin` (při špatných přihlašovacích údajích v loginu),
  - `Ex.BadRequestException` (ostatní chyby HTTP, 4xx/5xx).

- Příklady:
  - Přihlášení (form-url-encoded tělo a bez tokenu) nebo volání veřejných endpointů Bakalářů.

---

### Seznam škol (schools_list)

``` py
async def schools_list(self, town: str | None = None, recursive: bool = True) -> Schools | None:
```

- Parametry:
  - `town (str | None)`: volitelný filtr na název města.
  - `recursive (bool)`: způsob filtrování podle `town`:
    - `True` (výchozí): vybere města obsahující řetězec `town` kdekoliv v názvu,
    - `False`: vybere pouze města, jejichž název začíná na `town`.

- Chování:
  - Nejprve stáhne seznam měst z veřejného endpointu Bakalářů:
    - `https://sluzby.bakalari.cz/api/v1/municipality`
  - Pro každé (filtrované) město stáhne seznam škol a sestaví objekt `Schools`.
  - Počet souběžných dotazů na města je omezen parametrem `school_concurrency` nastaveným v konstruktoru `Bakalari` (výchozí 10).
  - Při úspěchu:
    - vrací instanci `Schools`,
    - zároveň uloží výsledek do `self.schools` (vedlejší efekt).
  - Při chybě vrací `None`.

- Poznámky:
  - Větší rozsah může znamenat stovky až tisíce požadavků (podle počtu měst); zvažte filtr `town` nebo kešování.
  - Objekt `Schools` lze uložit/načíst ze souboru (viz [třída Schools](./schools.md)):
    - `await schools.save_to_file("schools.json")`
    - `await Schools().load_from_file("schools.json")`

- Příklady:
  ``` py linenums="1"
  from async_bakalari_api import Bakalari

  bakalari = Bakalari()
  # všechny školy (doporučeno ukládat do souboru)
  schools = await bakalari.schools_list()
  if schools:
      await schools.save_to_file("schools.json")

  # pouze města začínající na 'Praha'
  schools = await bakalari.schools_list(town="Praha", recursive=False)

  # substring vyhledávání měst
  schools = await bakalari.schools_list(town="Brno")  # např. 'Brno' kdekoliv v názvu města
  ```

Základní modul `Bakalari` se stará o komunikaci endpointů se serverem školy.
Udržuje `Credentials`, provádí první přihlášení a umožňuje stáhnout [platný seznam škol](seznam_skol.md), ke kterým se lze připojit.

## třída Bakalari

``` py linenums="1" title="class Bakalari"

class Bakalari (self,
    server: str | None = None,
    credentials: Credentials | None = None,
    auto_cache_credentials: bool = False,
    cache_filename: str | None = None,
    session: aiohttp.ClientSession | None = None,
    school_concurrency: int = 10,
):
```

!!! notice "Jako argumenty třída přijímá:"

    * server (str | None): adresa serveru školy, se kterou chceme komunikovat
    * credentials (Credentials | None): volitelné předání hotových přihlašovacích údajů; pokud nejsou předány, vytvoří se prázdné `Credentials`
    * auto_cache_credentials (bool, optional): umožňuje automatické ukládání `access_tokenu` a `refresh_tokenu` do souboru a jejich možné opětovné použití při dalším běhu programu
    * cache_filename (str | None, optional): pokud je nastaveno automatické ukládání tokenů, pak je nutné zadat i jméno souboru, kam se mají tokeny ukládat
    * session (aiohttp.ClientSession | None, optional): volitelně lze předat existující HTTP session; pokud není zadána, klient si spravuje vlastní
    * school_concurrency (int, optional): maximální počet souběžných dotazů na města při sestavování seznamu škol; výchozí hodnota je 10

!!! danger "Exception"
    třída vrací chybu `Ex.CacheError`, pokud je povoleno automatické ukládání `Credentials` a není vyplněné `cache_filename`

!!! note "Credentials jsou read-only a chování auto-cache"
    Vlastnost `Bakalari.credentials` je pouze pro čtení. Přímé přiřazení není možné (vyvolá `AttributeError`). Pro získání/obnovu tokenů použijte metody jako `first_login(...)` nebo automatické obnovení při autorizovaných požadavcích.
    
    Pokud je zapnuto `auto_cache_credentials=True` a je nastaveno `cache_filename`, klient se při inicializaci pokusí `Credentials` automaticky načíst ze souboru a po každém obnovení tokenů je do něj také ukládá.

### Inicializace třídy

Třídu lze inicializovat bez zadání parametrů jako je `server`, nicméně, pak lze stahovat jen seznam škol, popřípadě zadávat neautorizované dotazy přímo na server `bakalari.cz`

!!! example "Inicializace třídy Bakalari"
    === "s kešováním"
        ``` py linenums="1"
        from async_bakalari_api import Bakalari

        bakalari = Bakalari("http://server_skoly.cz",
            auto_cache_credentials=True,
            cache_filename="credentials_cache.json")
        ```

    === "bez kešování"
        ``` py linenums="1"
        from async_bakalari_api import Bakalari

        bakalari = Bakalari("http://server_skoly.cz")
        ```
