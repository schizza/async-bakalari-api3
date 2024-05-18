# async Bakaláři API v3

!!! warning "Upozornění"
    Tato API je stále vyvíjena, a proto podporuje jen malé množství endpointů. Nicméně moduly zveřejněné v této dokumentaci jsou již stabilní.

`async Bakaláři API v3` je asynchronní klient pro komunikaci se školami, které jsou zapojeny do programu Bakaláři.
Seznam všech škol zapojených do programu Bakaláři lze získat též z [tohoto modulu](bakalari/seznam_skol.md).

## Instalace

Modul lze nainstalovat jako balíček z [PyPI](https://PyPi.org) nebo stáhnout z GitHubu.

!!! note ""
    Minimální verze Pythonu pro tento balíček je 3.12

=== ":simple-pypi: PyPI"

    ```shell
    python3 -m pip install async_bakalari_api
    ```

=== ":octicons-mark-github-16: GitHub"

    ```
    python3 -m pip install "git+https://github.com/schizza/async-bakalari-api3.git#egg=async-bakalari-api"
    ```
!!! tip "CLI"
    Po instalaci balíčku je dostupné jednoduché [CLI - `bakalari`](./cli/index.md)
