# modul Bakalari

Základní modul `Bakalari` se stará o komunikaci endpointů se serverem školy.
Udržuje `Credentials`, provádí první přihlášení a umožňuje stáhnout [platný seznam škol](seznam_skol), ke kterým se lze připojit.

## třída Bakalari

``` py linenums="1" title="class Bakalari"

class Bakalari (self, 
    server = str | None = None, 
    auto_cache_credentials: bool = False, 
    cache_filename: str | None = None):
```

!!! notice "Jako argumenty třída přijímá:"

    * server (str): adresa serveru školy, se kterou chceme komunikovat
    * auto_cache_credentials (bool, optional): umožňuje automatické ukládání `access_tokenu` a `refresh_tokenu` do souboru a jejich možné opětovné použití při dalším běhu programu
    * cache_filename (str, optional): pokud je nastaveno automatické ukládání tokenů, pak je nutné zadat i jméno souboru, kam se mají tokeny ukládat.

!!! danger "Exception"
    třída vrací chybu `Ex.CacheError`, pokud je povoleno automatické ukládání `Credentials` a není vyplněné `cache_filename`

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
