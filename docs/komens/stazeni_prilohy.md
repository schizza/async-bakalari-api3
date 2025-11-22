# Stažení přílohy zprávy

Zprávy v Komens mohou obsahovat přílohy, které mají své `ID` (typ `str`). Stažení přílohy je možné příkazem `Komens.get_attachment`.

```py
    async def get_attachment(self, id: str) -> tuple[str, bytes]:
```

!!! notice ""
    Vrací tuple (filename: str, filedata: bytes)

!!! danger ""
    Při chybě vrací False (např. expirované/invalidní tokeny, síťová chyba apod.). Volání je autorizované; při expirovaném access tokenu se provede automatický refresh přes refresh token a požadavek se zopakuje.

=== "Py"

    ```py linenums="1" title="Příklad uložení přílohy do souboru."
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")
        komens = Komens(bakalari)

        filename, filedata = await komens.get_attachment("ID_přílohy")

        with open(filename, "wb") as fi:
            fi.write(filedata)
    ```
=== "CLI"
    ``` shell
    # přihlaš se automaticky pomocí tokenů (--autocache)
    # načti školy ze souboru skoly.json (-sf)
    # použij url školy "škola"
    # z komens stáhni zprávy (--messages)
    # ulož přílohu s ID přílohy 1

    bakalari --auto_cache credentials.json -sf skoly.json -s "škola" komens --messages --attachment 1
    ```
