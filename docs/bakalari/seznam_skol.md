# Seznam škol

!!! warning ""
    Seznam škol je poměrně dlouhý a není vhodné ho stahovat při každém načtení modulu. Seznam škol je kešovatelný pomocí funkcí `save_to_file` a `load_from_file`, obě funkce jsou v modulu `datastructure`

``` py
async def async_schools_list(self) -> Schools:
```

!!! notice ""
    Při úspěšném stažení vrací `Schools`, pokdu seznam nelze stáhnout, vrací `None`
[Více o třídě `Schools`](../../bakalari/schools)

!!! example "Příklad použití"
    === "Načtení škol ze serveru"
        ```py linenums="1"
        from async_bakalari_api import Bakalari

        seznam_skol = await Bakalari().async_schools_list()
        ```

    === "Načtení ze souboru"
        ```py linenums="1"
        from async_bakalari_api import Schools

        schools: Schools = await Schools().load_from_file("schools_data.json")
        ```

    === "Použití s Bakalari"
        ```py linenums="1"
        from async_bakalari_api import Bakalari, Schools

        schools: Schools = await Schools().load_from_file("schools_data.json")
        bakalari = Bakalari(schools.get_url("Jméno školy/část jména školy"))
        ```
