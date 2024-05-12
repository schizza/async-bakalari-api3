# Přihlášení jménem a heslem (první přihlášení)
```py
async def first_login(self, username: str, password: str) -> Credentials:
```

!!! danger "Exceptions"
    Pokud jsou zadány špatné přístupové údaje vyvolá funkce výjimku `Ex.InvalidLogin`
    
Pro získání nového `access_tokenu` a `refresh_tokenu` se používá funkce `first_login`. Tato funkce se taktéž volá při vypršení `refresh_tokenu`, kdy již nelze automaticky získat `access_token`.

Zavoláním `first_login` se `Credentials` uloží do `Bakalari.credentials` a zároveň jsou nové přístupové údaje vráceny zpět, pokud je chcete ukládat někam do databáze.

!!! notice "Automatické ukládání přístupových údajů"
    Pokud je zapnutá funke `auto_cache_credentials`, pak se při každém autorizovaném požadavku na server obnovuje `access_token` i `refresh_token` a tyto se automaticky ukládají do zvoleného souboru.