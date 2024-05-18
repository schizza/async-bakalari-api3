# Stažení přílohy zprávy

Zprávy v Komens mohou obsahovat přílohy, které mají své `ID`. Stažení přílohy je možné příkazem `Komens.get_attachment`

```py
    async def get_attachment(self, id: str) -> Any:
```

!!! notice ""
    Vrací [filename, filedata]

!!! danger ""
    Při chybě vrací False

=== "Py"

    ```py linenums="1" title="Příklad uložení přílohy do souboru."
        from async_bakalari_api import Bakalari
        from async_bakalari_api.komens import Komens

        bakalari = Bakalari("http://server")
        bakalari.load_credentials("credentials.json")
        komens = Komens(bakalari)

        data = await komens.get_attachment("ID_zprávy")

        with open(data[0], "wb") as fi:
            fi.write(data[1])
    ```
=== "CLI"
    ``` shell
    # přihlaš se automaticky pomocí tokenů (--autocache)
    # načti školy ze souboru skoly.json (-sf)
    # z komens stáhni zprávy (--messages)
    # ulož přílohu s ID přílohy 1

    bakalari --auto_cache credentials.json -sf skoly.json komens --messages --attachment 1
    ```
