# async Bakaláři API v3

!!! warning "Upozornění"
    Tato API je stále vyvíjena, a proto podporuje jen malé množství endpointů. Nicméně moduly zveřejněné v této dokumentaci jsou již stabilní.

`async Bakaláři API v3` je asynchronní klient pro komunikaci se školami, které jsou zapojeny do programu Bakaláři. Aplikace je napsána kompletně v Pythonu.

Má taktéž zabudovaný [modul pro příkazovou řádku](cli/index.md) `CLI` k jednoduchému.

Seznam všech škol zapojených do programu Bakaláři lze získat též z [tohoto modulu](bakalari/seznam_skol.md).

## Instalace

Modul lze nainstalovat jako balíček z [PyPI](https://pypi.org/project/async-bakalari-api/) nebo stáhnout z GitHubu.

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
