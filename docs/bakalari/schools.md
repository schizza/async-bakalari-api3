# Třída Schools

Třída Schools je určena pro uchování seznamu škol a jejich URL pro Bakalari API.

Umožňuje vyhledat školu/y

* podle jména školy nebo části jména školy
* vyhledá školy podle města
* lze hledat i podle URL endpointu

!!! notice "Poznámka"
    Třída Schools uchovává položky v seznamu `Schools.school_list` jako instance třídy `Schools`

``` py linenums="1"
@dataclass
class School:
    """Data structure for one school item."""

    name: str = None
    api_point: str = None
    town: str = None
```
## Metody třídy `Schools`

### append_school

``` py
    def append_school(self, name: str, api_point: str, town: str) -> bool: 
```
Slouží k jednoduchému přidání nové školy do seznamu škol. Všechny argumeny jsou povinné a nesmí být `None` nebo prázdný řetězec.

!!! note ""
    Vrací `True` nebo `False`

### get_url

``` py linenums="1"
    def get_url(self, name: str | None = None, idx: int | None = None) -> str | False:
        """Return url of school from name or index in dictionary.

        Only one must be specified - name or index, otherwise returns False
        If name or index is not found in dictionary returns False.
        """
```
Vrací URL pro školu podle jména, části jména (část jména musí být jedinečná) nebo indexu ve slovníku.

!!! note ""
    Vrací URL školy pokud škola exituje, jinak `False`

### get_schools_by_town

```py
    get_schools_by_town(self, town: str | None = None) -> list[School]
```

Vrací seznam škol v daném městě.

!!! note ""
    Vrací `list[School]` nebo `None` pokud město neexituje.

### get_school_name_by_api_point

```py
    def get_school_name_by_api_point(self, api_point: str) -> str | bool
```

Vrací název školy podle jejího API.

### save_to_file

```py
    def save_to_file(self, filename: str) -> bool
```

Ukládá načtený seznam škol do souboru ve formátu JSON.

!!! note ""
    Při chybě parsování JSON nebo chybě zápisu vrací `False`, jinak `True`

### load_from_file

```py
    def load_from_file(self, filename: str) -> Schools
```

Načte seznam škol ze souboru v JSON formátu.

!!! note ""
    Vrací `Schools` s načtenými školami, při chybě parsování JSON nebo chybě otevření souboru vrací `False`
