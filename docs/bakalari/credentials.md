# Credentials
Samotné tokeny i s `username` i `user_id` lze spravovat přes proměnou `Bakalari.credentials`

!!! warning ""
    Heslo se do kešovacího souboru neukládá, není dostupné ani v proměnné `credentials`

Pojďme se kouknout na třídu `Credentials`, která se nachází v `async_bakalari_api.datastructure`

??? note "class Credentials"
    ``` py linenums="1"
        @dataclass(frozen=True)
        class Credentials:
            """Credentials holder."""

            username: str | None = None
            access_token: str | None = None
            refresh_token: str | None = None
            user_id: str | None = None

            @classmethod
            def create(cls, data: dict[str, Any]) -> Credentials:
                ...

            @classmethod
            def create_from_json(cls, data: dict[str, Any]) -> Credentials:
                """Return class object from JSON dictionary."""
                ...
    ```
Přistupovat k aktuálním datům lze z instance `Bakalari`

``` py linenums="1"
    username = bakalari.credentials.username
    access_token = bakalari.credentials.access_token
    refresh_token = bakalari.credentials.refresh_token
    user_id = bakalari.credentials.user_id
```

Hodnoty v `Bakalari.credentials` jsou pouze pro čtení. Nové údaje předávejte při vytvoření instance `Bakalari` přes parametr `credentials`, nebo použijte `first_login(...)` či `load_credentials(...)`. Převod dat z payloadu serveru usnadňují metody `create` a `create_from_json()` (preferována).

U metody `create()` se předpokládá datové pole takové, které zasílá přímo server:

=== "create()"
    ``` py linenums="1"

        from async_bakalari_api.datastructure import Credentials
        from async_bakalari_api import Bakalari

        # payload tak, jak ho vrací server (klíče včetně 'bak:UserId')
        nove_udaje = {
            "bak:UserId": "user_id",
            "access_token": "nový access_token",
            "refresh_token": "nový refresh_token",
            "username": "nové username"
        }

        creds = Credentials.create(nove_udaje)
        bakalari = Bakalari(server="http://server", credentials=creds)
    ```
=== "create_from_json()"
    ```py linenums="1"
        
        from async_bakalari_api.datastructure import Credentials
        from async_bakalari_api import Bakalari

        nove_udaje = {
            "user_id": "nové user_id",
            "access_token": "nový access_token",
            "refresh_token": "nový refresh_token",
            "username": "nové username"
        }

        creds = Credentials.create_from_json(nove_udaje)
        bakalari = Bakalari(server="http://server", credentials=creds)
    ```

## Nahrání uložených údajů

Jak již bylo řečeno, `Bakalari` umožňují automatické ukládání `Credentials` do souboru ve formátu `json`

Jejich získání zpět je možné pomocí metody `load_credentials`

!!! notice def "load_credentials(self, filename: str) -> Credentials | bool"
    Jako argument se zadává jméno souboru.
    Vrací `Credentials`, které také hned ukládá do `Bakalari.credentials`

!!! danger ""
    Při neúspěchu vrací `False`

Po zvolání metody `load_credentials` máme tedy v instanci `bakalari` aktuální údaje a lze je využít rovnou při přihlášení.

```py linenums="1"
    from async_bakalari_api.datastructure import Schools
    from async_bakalari_api import Bakalari

    school: Schools = await Schools().load_from_file("schools_data.json")
    bakalari = Bakalari(
        server=school.get_url("část jména školy"), 
        auto_cache_credentials=True,
        cache_filename="credentials.json"
    )
    bakalari.load_credentials("credentials.json")

    ... nyní již můžeme provádět autorizované dotazy na server školy
```
