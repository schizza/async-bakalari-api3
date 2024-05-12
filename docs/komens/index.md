#Modul Komens

Tento modul slouží k získání přijatých zpráv ze serveru školy.
Tento modul již provádí autorizované dotazy, takže je nutné již mít údaje o [tokenech](../bakalari/credentials), případně provést [první přihlášení](../bakalari/first_login).

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

Načtení zpráv probíhá metodou `Komens.get_messages()`

Tato metoda vrátí všechny zprávy, které jsou uložené na serveru školy a ukládá je do třídy `Messages`, kde každá zpráva je uložena jako `MessageContainer`.

```py
Messages = list[MessageContainer]
```

!!! notice "Messages"
    ke zprávám lze přistupovat z instance `Komens.messages`

Více o `Messages` a `MessageContainer` bude k dispozici Dev dokumentaci později.
Pro užití v běžném režimu není třeba se jimi zabývat do hloubky.

```py linenums="1" hl_lines="6" title="Načtení zpráv se serveru"
    from async_bakalari_api import Bakalari
    from async_bakalari_api.komens import Komens

    bakalari = Bakalari("http://server")
    bakalari.load_credentials("credentials.json")

    komens = Komens(bakalari)
    await komens.get_messages()
```
