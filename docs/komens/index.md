# Modul Komens

Tento modul slouží k získání přijatých zpráv ze serveru školy.
Tento modul již provádí autorizované dotazy, takže je nutné již mít údaje o [tokenech](../bakalari/credentials.md), případně provést [první přihlášení](../bakalari/first_login.md).

```py linenums="1"
    class Komens:
    """Class for working with Komens messages."""

    def __init__(self, bakalari: Bakalari):
        """Initialize class Komens."""
        self.bakalari = bakalari
        self.messages = Messages()
```
!!! notice ""
    Jako jediný parametr přijímá inicializovanou instanci `Bakalari`

    ``` py  
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")

        komens = Komens(bakalari)
    ```

## Načtení přijatých zpráv

Načtení zpráv probíhá metodou `Komens.fetch_messages()`.

Tato metoda nejprve vymaže dosud uložené zprávy a stáhne aktuální zprávy ze serveru školy. Vrací instanci `Messages` (seznam `MessageContainer`) a zároveň ji uloží do `Komens.messages`.

```py
Messages = list[MessageContainer]
```

!!! notice "Messages"
    ke zprávám lze přistupovat z proměnné `Komens.messages`

Více o `Messages` a `MessageContainer` bude k dispozici Dev dokumentaci později.
Pro užití v běžném režimu není třeba se jimi zabývat do hloubky.

## Nepřečtené zprávy

- Získat seznam nepřečtených zpráv:

```py
async def get_unread_messages(self) -> list[MessageContainer]:
```

Vrátí list pouze těch zpráv, které mají `read=False`. Pokud dosud nejsou zprávy načtené, metoda si je nejprve stáhne.

- Získat počet nepřečtených zpráv:

```py
async def count_unread_messages(self) -> int:
```

Vrací počet nepřečtených zpráv; využívá přímý endpoint (není nutné mít zavolané `fetch_messages()`).

```py linenums="1" hl_lines="6" title="Načtení zpráv ze serveru"
    from async_bakalari_api import Bakalari
    from async_bakalari_api.komens import Komens

    bakalari = Bakalari("http://server")
    bakalari.load_credentials("credentials.json")

    komens = Komens(bakalari)
    await komens.fetch_messages()
```
