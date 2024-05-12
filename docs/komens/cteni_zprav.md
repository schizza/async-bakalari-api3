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
        for msg in zpravy_ze_dne:
            print(msg.text)
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
        for msg in zpravy_ze_dne:
            print(msg.text)
    ```
