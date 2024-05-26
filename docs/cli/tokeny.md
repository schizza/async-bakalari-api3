# Přihlášení a získání tokenů

Přihlášení k serveru školy lze provést trojím způsobem.

* použitím jména a hesla `-F`
* použitím souboru s tokeny (tyto se ale automaticky neukádají) `-C -cf`
* použitím automatického kešování tokenů `--auto_cache`

!!! danger "Nutné parametry školy!"
    Pro přihlášení je nutné zadat, ke které škole se přihlašujete.

    Je tedy nutné vždy použít parametr `-s ŠKOLA` popřípadě s parameterm seznamu škol `-s ŠKOLA -sf seznam_skol.json`

!!! notice "Automatické vytvoření konfiguračního souboru"
    Od verze 0.3.3 je možné vytvoření konfiguračního souboru s tokeny a API pointem školy.

    Při prvním přihlášení lze použít 
    ```bakalari -a -F JMENO HESLO -t MĚSTO -s ŠKOLA``` 
    tím se vytvoří konfukurační soubor a soubor s tokeny, které se budou automaticky načítat při dalším použitím `-a` bez nutnosti zadávání `-s`, `-sf`, `--auto_cache`, `-cf`

=== "Automatické uložení"
    ```shell
    bakalari -a -f JEMENO HESLO -t MĚSTO -s ŠKOLA
    ```

=== "Přihlášení heslem a zapsání tokenů do souboru"
    ```shell
    bakalari -F JMENO HESLO -cf tokeny.json -s ŠKOLA -t MĚSTO
    ```

=== "Přihlášení pomocí tokenů bez kešování"
    ```shell
    bakalri -C -cf tokeny.json -s ŠKOLA -sf seznam_škol
    ```

=== "Přihlášení s autmatickým kešováním"
    ```shell
    bakalari --auto_cache tokeny.json -s ŠKOLA -sf seznam_škol
    ```
