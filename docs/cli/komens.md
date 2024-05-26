# Zprávy (Komens)

```shell
bakalari komens -h
usage: bakalari komens [-h] [-u] [-sa] [-l | -e ID_zprávy | -s SOUBOR] [--attachment ID_přílohy]

options:
  -h, --help            show this help message and exit
  -u, --unread          Vypíše nepřečtené zprávy
  -sa, --save_attachment
                        Uloží automaticky přílohy zpráv do souboru
  -l, --list            Vypíše přijaté zprávy
  -e ID_zprávy, --extend ID_zprávy
                        Vypíše podrobně zprávu s ID zprávy.
  -s SOUBOR, --save SOUBOR
                        Uloží zprávy do souboru
  --attachment ID_přílohy
                        Stáhne přílohu zprávy.
```

!!! danger "Přihlášení"
    K využití Komens již musíme mít přihlášení ke škole v podobě buď jméno/helso nebo platné tokeny. Jejich získání je posáno [zde](tokeny.md)

=== "Výpis všech zpráv do terminálu"
    ```shell
    bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens -l
    ```

=== "Uložení všech zpráv do souboru"
    ```shell
    bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens -s zpravy.json
    ```

Pokud jsou na severu nepřečetné zprávy, lze je získat použitím `-u`

=== "Výpis nepřečtených zpráv"
    ```shell
    bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens -u -l
    ```

=== "Uložení nepřečtených zpráv"
    ```shell
        bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens -u -s zpravy.json"
    ```

## Přílohy

Přílohy zpráv lze stáhnout buď jednotlivě, pokud znáte `ID` přílohy nebo automaticky, pokud zpráva přílohy obsahuje.

=== "Stažení prílohy"
    ```shell
    bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens --attachment ID
    ```

=== "Automatické stažení přílohy"
    ```shell
    bakalari --auto_cache tokeny.json -sf seznam_skol.json -s "Gymnázium Židlochovice" komens -l -sa
    ```