# Přihlášení jménem a heslem (první přihlášení)
```py
async def first_login(self, username: str, password: str) -> Credentials:

async def refresh_access_token(self) -> Credentials:
```

!!! danger "Exceptions"
    - first_login: při neplatných přihlašovacích údajích vyvolá `Ex.InvalidLogin`
    - refresh_access_token: pokud není dostupný `refresh_token` nebo je expirovaný/neplatný, vyvolá `Ex.RefreshTokenExpired`
    
Pro získání nového `access_tokenu` a `refresh_tokenu` se používá funkce `first_login`. Tato funkce se taktéž volá při vypršení `refresh_tokenu`, kdy již nelze automaticky získat `access_token`.

Zavoláním `first_login` se `Credentials` uloží do `Bakalari.credentials` a zároveň jsou nové přístupové údaje vráceny zpět, pokud je chcete ukládat někam do databáze.

!!! notice "Automatické ukládání přístupových údajů"
    Pokud je zapnutá funkce `auto_cache_credentials` a je zadán `cache_filename`:
    - při inicializaci se klient pokusí načíst `Credentials` ze souboru,
    - po úspěšném `first_login()` se nové tokeny uloží do souboru,
    - při automatickém obnovení přes `refresh_access_token()` se aktualizované tokeny také uloží.

    Poznámky:
    - autorizované požadavky při expirovaném/invalidním `access_token` spustí automatický refresh a požadavek se provede znovu (max. 1 pokus),
    - pokud není dostupný platný `refresh_token`, obnovení selže s `Ex.RefreshTokenExpired` a je potřeba znovu zavolat `first_login()`,
    - vlastnost `Bakalari.credentials` je pouze pro čtení; aktualizuje se interně po `first_login()`/`refresh_access_token()`.