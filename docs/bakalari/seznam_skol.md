# Seznam škol

Seznam škol je v modulu `async_bakalari_api.datastructure`

``` py
async def schools_list(self) -> Schools:
```

!!! danger "Omezení dotazů"
    Seznam škol je poměrně dlouhý: **3105** škol v **1208** městech, tedy i 1208 dotazů na server Bakalářů.
    
    Není tak vhodné stahovat celý seznam při každém načtení modulu. Seznam škol je kešovatelný pomocí metod `save_to_file` a `load_from_file`

    Další možností, jak omezit počet dotazů je použití parametru `town` při volání funkce

    ``` py linenums="1"
    schools: Schools = bakalari.school_list(town="požadované město")
    ```

!!! notice ""
    Při úspěšném stažení vrací `Schools`, pokdu seznam nelze stáhnout, vrací `None`
[Více o třídě `Schools`](../bakalari/schools.md)

!!! example "Příklad použití"
    === "CLI"
        ``` shell
        # uložení celého seznamu škol do souboru
        bakalari -N schools -s "skoly.json"

        #vypsání škol z určitého města
        bakalari -N -t "město" schools -l
        ```
    === "Načtení škol ze serveru"
        ```py linenums="1"
        from async_bakalari_api import Bakalari

        seznam_skol = await Bakalari().schools_list()
        ```

    === "Načtení ze souboru"
        ```py linenums="1"
        from async_bakalari_api.datastructure import Schools

        schools: Schools = await Schools().load_from_file("skoly.json")
        ```

    === "Použití s Bakalari"
        ```py linenums="1"
        from async_bakalari_api import Bakalari
        from async_bakalari_api.datastructure import Schools

        schools: Schools = await Schools().load_from_file("schools_data.json")
        bakalari = Bakalari(schools.get_url("Jméno školy/část jména školy"))
        ```
