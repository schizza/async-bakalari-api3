# CLI (Command Line Interface)

Balíček `async_bakalari_api` pokytuje také uživatelské rozhraní pro příkazovou řádku `CLI`.

Po [instalaci](../index.md#instalace) ja automaticky dostupný příkaz `bakalari` z terminálu nebo příkazové řádky.

Nápověda k užití `bakalari` se vyvolá příkazem `bakalari -h`

```shell
bakalari -h

usage: bakalari [-h] [-N] [-F jméno heslo] [-Ff SOUBOR] [-C] [-cf soubor s tokeny] [--auto_cache soubor s tokeny]
                [-t Město] [-s ŠKOLA] [-sf SOUBOR.json] [-v]
                {schools,komens} ...

Bakalari DEMO App

options:
  -h, --help            show this help message and exit
  -t Město, --town Město
                        Omezí stahování a dotazy pouze na jedno město
  -s ŠKOLA, --school ŠKOLA
                        Název školy nebo část názvu školy
  -sf SOUBOR.json, --schools_file SOUBOR.json
                        Načte seznam škol ze zadaného souboru (formát JSON)
  -v, --verbose         Zapne podrobné logování

Přihlášení (požadováno):
  Zvolte typ přihlášení heslo / tokenu

  -N, --no_login        Provede neautorizovaný přístup
  -F jméno heslo, --first_login jméno heslo
                        Provede přihlášení jménem a heslem. Pokud je zadán parametr -cf, pak zapíše tokeny do tohoto
                        souboru. Jinak tokeny zobrazí na výstup. Pokud je použit parametr --auto_cache, pak se tokeny
                        zapíší do tohoto souboru i do souboru zadaného v parametru -cf. Škola může být pouze část
                        názvu, ale název musí být jedinečný v seznamu škol. Pro rychlejší vyhledávání můžete přidat
                        parametr -t k vyhledávání pouze ve zvoleném městě.
  -Ff SOUBOR, --first_login_file SOUBOR
                        Přihlášení se jménem a heslem načtených ze souboru. Soubor s přihlašovacím jménem a heslem ve
                        formátu JSON.
  -C, --credentials     Přihlášení pomocí tokenu. Vyžaduje parametr -cf
  -cf soubor s tokeny, --credentials_file soubor s tokeny
                        Jméno souboru odkud se maji načíst tokeny.
  --auto_cache soubor s tokeny
                        Použít automatické kešování tokenů. Povinný je parametr jméno souboru do kterého se má kešovat.

Seznam příkazů:
  {schools,komens}
    schools             Seznam škol
    komens              Komens
```