# Stažení seznamu škol

```shell
usage: bakalari schools [-h] (-l | -s Jméno souboru (formát JSON))

options:
  -h, --help            show this help message and exit
  -l, --list            Vypíše seznam všech škol. S parameter -t vypíše školy ze zvoleného města.
  -s Jméno souboru (formát JSON), --save Jméno souboru (formát JSON)
                        Uloží seznam škol do souboru.
```

!!! note ""
    K pouhému stažení seznamu škol nepotřebujeme přihlášení. Můžeme proto využít parametr `-N` pro neutorizované dotazy.

=== "Zobrazení kompletního seznamu"

    ```shell
    bakalari -N schools --list
    ```
=== "Stažení komplezního seznamu do souboru"

    ```shell
    bakalari -N schools --list -s seznam_skol.json
    ```

!!! note "Omezení na město"
    Pokud chcete výsledky hledání omezit pouze na určité město, pak lze použít parametr `-t`

```shell
bakalari -N -t Ostrava schools -l
```

!!! danger ""
    Hledání v seznamu škol je rekursivní. Znamaná to tedy, že při zadání `-t Ostrava` se vyhledají všechna města, která obsahují `Ostrava`. Tedy i `Moravská Ostrava` nebo `Slezská Ostrava`.

    Stejně tak, pokud se zadá pouze část názvu města, např. `Prostěj` vyhledá `Prostejov`, ale i `Brodek u Prostějova`.

