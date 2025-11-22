# Seznam škol

Seznam škol se získává metodou na třídě `Bakalari`. Samotná datová struktura seznamu je `Schools` (viz `async_bakalari_api.datastructure`).

``` py
async def schools_list(self, town: str | None = None, recursive: bool = True) -> Schools | None:
```

- Parametry:
  - `town (str | None)`: volitelný filtr na název města.
  - `recursive (bool)`: způsob filtrování podle `town`:
    - `True` (výchozí): vybere města, která obsahují řetězec `town` kdekoliv v názvu.
    - `False`: vybere pouze města, jejichž název začíná na `town`.

- Chování:
  - Metoda volá veřejný endpoint Bakalářů pro seznam měst a pro každé vybrané město stáhne školy.
  - Po úspěchu vrací instanci `Schools` a zároveň ji uloží do `self.schools`.
  - Při chybě vrací `None`.

!!! tip "Souběžné dotazy"
    Počet souběžných dotazů na města při sestavování seznamu škol je omezen parametrem `school_concurrency` v konstruktoru `Bakalari` (výchozí 10).

!!! danger "Omezení dotazů"
    Seznam škol je poměrně dlouhý: **3105** škol v **1208** městech, tedy i 1208 dotazů na server Bakalářů.
    
    Nedoporučuje se stahovat celý seznam při každém spuštění. Místo toho:
    - použijte filtr `town` (a volitelně `recursive=False` pro prefixové vyhledávání),
    - ukládejte výsledek do souboru pomocí metod `save_to_file` / `load_from_file`.

    ``` py linenums="1"
    # filtr dle města (substring)
    schools: Schools | None = await bakalari.schools_list(town="požadované město")
    ```

!!! notice ""
    Při úspěchu vrací `Schools`, při chybě `None`.  
    [Více o třídě `Schools`](../bakalari/schools.md)

!!! example "Příklad použití"
    === "CLI"
        ``` shell
        # uložení celého seznamu škol do souboru
        bakalari -N schools -s "skoly.json"

        # vypsání škol z určitého města
        bakalari -N -t "město" schools -l
        ```
    === "Načtení škol ze serveru"
        ```py linenums="1"
        from async_bakalari_api import Bakalari

        bakalari = Bakalari()
        seznam_skol = await bakalari.schools_list()
        ```
    === "Načtení jen měst začínajících na 'Praha'"
        ```py linenums="1"
        from async_bakalari_api import Bakalari

        bakalari = Bakalari()
        praha_skoly = await bakalari.schools_list(town="Praha", recursive=False)
        ```
    === "Uložení/načtení ze souboru"
        ```py linenums="1"
        from async_bakalari_api.datastructure import Schools

        # uložení
        schools = await Bakalari().schools_list()
        if schools:
            await schools.save_to_file("skoly.json")

        # načtení
        schools_from_file: Schools = await Schools().load_from_file("skoly.json")
        ```
    === "Použití s Bakalari"
        ```py linenums="1"
        from async_bakalari_api import Bakalari
        from async_bakalari_api.datastructure import Schools

        schools: Schools = await Schools().load_from_file("schools_data.json")
        bakalari = Bakalari(schools.get_url("Jméno školy/část jména školy"))
        ```
