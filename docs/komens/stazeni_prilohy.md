# Stažení přílohy zprávy

Zprávy v Komens mohou obsahovat přílohy, které mají své `ID`. Stažení přílohy je možné příkazem `Komens.get_attachment`

```py
    async def get_attachment(self, id: str) -> Any:
```

!!! notice ""
    Vrací [filename, filedata]

!!! danger ""
    Při chybě vrací False

```py linenums="1" title="Příklad uložení přílohy do souboru."
    from async_bakalari_api import Bakalari
    from async_bakalari_api.komens import Komens

    bakalari = Bakalari("http://server")
    bakalari.load_credentials("credentials.json")
    komens = Komens(bakalari)

    data = await komens.get_attachment("ID_zprávy")

    with open(data[0], "wb") as fi:
        fi.write(data[1])
        fi.close()
```
