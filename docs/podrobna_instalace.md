# Podrobná instalace

Aplikace je kompletně napsána v `Pythonu` verze 3.12

Jak naistalovat Python přesahuje tuto dokumentaci, ale jednoduché postupy jsou k dispozici [napříkalad zde.](https://naucse.python.cz/lessons/beginners/install/)

## Nové virtuální prostředí

Pokud máte již nainstalovaný Python vytvořte nové virtuální prostřední ve složce, kde chcete pracovat s `async_bakalari_api`

=== "Mac/Linux"

    ```zsh
    mkdir ~/bakalari_test
    cd ~/bakalari_test

    python3 -m venv .venv
    ```

=== "Windows"

    ```powershell
    mkdir bakalari_test
    cd bakalari_test

    py -3 -m venv venv
    ```

Virtuální prostředí se musí vždy před použitím aktivovat.

=== "Mac/Linux"
    ```zsh
    source .venv/bin/acitvate
    ```

=== "Windows"
    ```powershell
    venv\Scripts\activate
    ```

!!! note ""
    Po aktivaci virtuálního prostředí se již příkazy nemění v závislosti na systému.

```py title="Instalace balíčku `async_bakalari_api`"

python3 -m pip install async_bakalari_api

```

Nyní již můžete využívat [`CLI`](cli/index.md)
