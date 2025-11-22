# CLI (Command Line Interface)

Balíček `async_bakalari_api` poskytuje také uživatelské rozhraní pro příkazovou řádku `CLI`.

Po [instalaci](../index.md#instalace) je automaticky dostupný příkaz `bakalari` z terminálu nebo příkazové řádky.

Nápověda k užití `bakalari` se vyvolá příkazem `bakalari -h`

```shell
bakalari -h

usage: bakalari [-h] [-N] [-F jméno heslo] [-Ff SOUBOR] [-C] [-cf soubor s tokeny] [--auto_cache soubor s tokeny]
                [-t Město] [-s ŠKOLA] [-sf SOUBOR.json] [-r | -nr] [-v]
                {schools,komens,timetable} ...

Bakalari DEMO App

options:
  -h, --help            show this help message and exit
  -t Město, --town Město
                        Omezí stahování a dotazy pouze na jedno město
  -s ŠKOLA, --school ŠKOLA
                        Název školy nebo část názvu školy
  -sf SOUBOR.json, --schools_file SOUBOR.json
                        Načte seznam škol ze zadaného souboru (formát JSON)
  -r, --recursive       Povolí rekurzivní (podřetězcové) vyhledávání (výchozí).
  -nr, --no-recursive   Zakáže rekurzivní vyhledávání (použije se pouze prefix).
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
  {schools,komens,timetable}
    schools             Seznam škol
    komens              Komens
    timetable           Rozvrh (timetable)
```

## Rozvrh (timetable)

```shell
bakalari timetable -h
usage: bakalari timetable [-h] [-p] [-d YYYY-MM-DD] [--class ID | --group ID | --teacher ID | --room ID | --student ID]

options:
  -h, --help            show this help message and exit
  -p, --permanent       Načte pevný (permanentní) rozvrh místo aktuálního.
  -d YYYY-MM-DD, --date YYYY-MM-DD
                        Datum týdne pro aktuální rozvrh ve formátu YYYY-MM-DD. Pokud není zadáno, použije se dnešní datum.
  --class ID            ID třídy (classId) pro zobrazení rozvrhu.
  --group ID            ID skupiny (groupId) pro zobrazení rozvrhu.
  --teacher ID          ID učitele (teacherId) pro zobrazení rozvrhu.
  --room ID             ID místnosti (roomId) pro zobrazení rozvrhu.
  --student ID          ID studenta (studentId) pro zobrazení rozvrhu.
```

!!! note ""
    Globální přepínače `-r/--recursive` a `-nr/--no-recursive` ovlivňují, jak se vyhledává škola/město (podřetězcově vs. pomocí prefixu).