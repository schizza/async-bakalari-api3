# Čtení přijatých zpráv

Pokud již máme zprávy staženy ze serveru, jsou uloženy v `Komens.messages`, který představuje seznam zpráv ve formátu `Messages`. Každá zpráva je reprezentována jako `MessageContainer`

## Celkový počet přijatých zpráv

``` py
    Komens.messages.count_messages()
```
!!! notice ""
    Vrací `int` jako celkový počet zpráv

## Zpráva podle data / rozsahu dat

Pokud chceme zobrazit zprávy jen z určitého dne nebo rozsahu dní, pak k tomu slouží metoda `get_messages_by_date()`

``` py
    def get_messages_by_date(
        self, date: dt, to_date: dt | None = None
    ) -> list[MessageContainer]:
        """Get messages by date.

        If `to_date` is set, then returns list of range from `date` to `to_date`
        """
```
=== "Den"
    ``` py linenums="1" hl_lines="11-13"
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens
        from datetime import datetime as dt

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")

        komens = Komens(bakalari)
        await komens.get_messages()

        zpravy_ze_dne = komens.messages.get_messages_by_date(dt.date.today())
        print(msg for msg in zpravy_ze_dne, end="\n --- \n")
        
    ```
=== "Rozsah dní"
    ``` py linenums="1" title="Zprávy za posledních 30 dní" hl_lines="11-16"
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens
        import datetime

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")

        komens = Komens(bakalari)
        await komens.get_messages()

        zpravy_ze_dne = komens.messages.get_messages_by_date(
                datetime.date.today() + datetime.timedelta(days=-30),
                to_date=datetime.date.today()
            )
        print(msg for msg in zpravy_ze_dne)
    ```

## Zpráva podle ID_zprávy

Pokud chceme přečíst konkrétní zprávu s `ID_zprávy` slouží k tomu metoda `get_message_by_id`

``` py
    def get_message_by_id(self, id: str) -> MessageContainer
```

=== "Py"
    ``` py linenums="1"
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")

        komens = Komens(bakalari)
        await komens.get_messages()

        zprava = komens.messages.get_messages_by_id(1)
        print(zprava)
    ```
=== "CLI"
    ``` shell
    # přihlášení pomocí tokenů (-C) ze souboru credentials.json (-cf)
    # školy načti ze souboru skoly.json (-sf)
    # a z komens načti zprávy (--messages) a vypiš zprávu s ID 1 (-e 1)

    baklari -C -cf credntials.json -sf skoly.json komens --messages -e 1
    ```
