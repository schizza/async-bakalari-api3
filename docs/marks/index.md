# Modul Marks

Modul `Marks` slouží k načítání a práci se známkami. Umí:
- stáhnout známky ze serveru školy,
- pracovat s předměty a jejich známkami (včetně nových známek),
- filtrovat známky podle data nebo rozsahu datumů,
- vracet známky seskupené podle předmětů,
- formátovaný výstup

Tento modul již provádí autorizované dotazy, takže je nutné již mít údaje o [tokenech](../bakalari/credentials.md), případně provést [první přihlášení](../bakalari/first_login.md).

## Třída Marks

``` py linenums="1" title="class Marks"
from async_bakalari_api import Bakalari

class Marks:
    """Marks class."""

    def __init__(self, bakalari: Bakalari): ...
```

!!! notice ""
    Jako jediný parametr přijímá inicializovanou instanci `Bakalari`.

    ``` py linenums="1"
    from async_bakalari_api import Bakalari
    from async_bakalari_api.marks import Marks

    bakalari = Bakalari("http://server")
    bakalari.load_credentials("credentials.json")

    marks = Marks(bakalari)
    ```

### Načtení známek ze serveru

Známky načte metoda `fetch_marks()`.

!!! notice ""
  Metoda se nevolá automaticky při inicializaci třídy `Marks`. Je nutné ji volat ručně vždy, když chcete aktualizovat známky.

``` py linenums="1" title="Načtení známek"
await marks.fetch_marks()
```

!!! danger "Upozornění"
    Pro správné fungování je nutné mít platné přihlašovací údaje (tokeny) v instanci `Bakalari`.

---

## Datové struktury

Známky a předměty se ukládají do speciálních tříd, které modul používá interně i v návratových hodnotách API:

- `SubjectsBase`
  - `id: str` — identifikátor předmětu
  - `abbr: str` — zkratka předmětu
  - `name: str` — název předmětu
  - `average_text: str` — textový průměr (řeší server)
  - `points_only: bool` — zda je předmět pouze bodově hodnocen
  - `marks: MarksRegistry` — kolekce známek pro daný předmět

- `MarksBase`
  - `id: str` - id známky
  - `date: datetime` - datum známky
  - `caption: str` - text známky
  - `theme: str | None` - název tématu známky
  - `marktext: MarkOptionsBase | None` — textová reprezentace známky (1, A, +, apod.)
  - `teacher: str | None` - učitel, který vydal známku
  - `subject_id: str` - identifikátor předmětu
  - `is_new: bool` - nová známka
  - `is_points: bool` - zda je známka bodová
  - `points_text: str | None` - textová reprezentace bodů
  - `max_points: int | None` - maximální počet bodů

- `MarkOptionsBase`
  - `id: str`
  - `abbr: str`
  - `text: str`

!!! notice "Logování a fallbacky"
    - Pokud server vrátí `MarkText`, který není v `MarkOptions`, do logu se zapíše warning a modul použije „placeholder“ `MarkOptionsBase`, aby zpracování nespadlo.
    - Pokud server vrátí známku k neznámému `subject_id`, modul to zaloguje jako warning a danou známku přeskočí.

---

## Základní čtení dat

### Získání seznamu předmětů

``` py linenums="1" title="Seznam předmětů"
subjects = await marks.get_subjects()
print(f"Načteno předmětů: {len(subjects)}")
for s in subjects:
    print(s.id, s.abbr, s.name, s.average_text, s.points_only)
```

### Získání známek pro konkrétní předmět

``` py linenums="1" title="Známky pro předmět"
subject_id = "SUBJECT_ID"
subject_marks = await marks.get_marks(subject_id)
for m in subject_marks:
    print(m.date.date(), m.caption, (m.marktext.text if m.marktext else ""))
```

---

## Práce s novými známkami

### Všechny nové známky (napříč předměty)

``` py linenums="1" title="Nové známky"
new_marks_grouped = await marks.get_new_marks()
for subj in new_marks_grouped:
    print(subj.name, f"({subj.abbr})")
    for m in subj.marks:
        print(" ", m.date.date(), m.caption)
```

### Nové známky podle dne nebo rozsahu

=== "Jeden den"

  ``` py linenums="1" title="Nové známky v rozsahu"
  from datetime import datetime
  
  # Jeden den
  day = datetime(2025, 9, 12)
  by_day = await marks.get_new_marks_by_date(date=day)
  ```
  
=== "Rozsah dní"
    ``` py linenums="1" title="Nové známky v rozsahu"
    from datetime import datetime
  
    # Rozsah včetně krajních dnů
    start = datetime(2025, 9, 1)
    end = datetime(2025, 9, 30)
    by_range = await marks.get_new_marks_by_date(date=start, date_to=end)

    # Jen pro konkrétní předmět
    by_subject = await marks.get_new_marks_by_date(date=start, date_to=end, subject_id="SUBJECT_ID")
    ```

---

## Kompletní přehled známek (seskupeno dle předmětů)

### Vrátit jako data

``` py linenums="1" title="Všechny známky (seskupené)"
groups = await marks.get_marks_all()
for subj in groups:
    print(subj.name, f"({subj.abbr})")
    for m in subj.marks:
        print(" ", m.date.date(), m.caption)
```

### Filtrovat dle data/rozsahu a/nebo předmětu

``` py linenums="1" title="Filtrace známek"
from datetime import datetime

# vše v jednom dni
text = await marks.format_all_marks(date=datetime(2025, 9, 12))

# v rozsahu dat
text = await marks.format_all_marks(date=datetime(2025, 9, 1), date_to=datetime(2025, 9, 30))

# pouze daný předmět
text = await marks.format_all_marks(subject_id="SUBJECT_ID")
print(text)
```

!!! tip "Výpis na stdout"
    Modul má i helper, který rovnou vypíše formátovaný přehled:
    ``` py linenums="1"
    await marks.print_all_marks()  # případně s filtry date/date_to/subject_id
    ```
