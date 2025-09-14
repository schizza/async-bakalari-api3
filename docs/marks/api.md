## Rychlá referenční API

``` py linenums="1" title="Hlavní metody"
class Marks:
    async def fetch_marks(self) -> None: ...
    async def get_subjects(self) -> list[SubjectsBase]: ...
    async def get_marks(self, subject_id: str) -> list[MarksBase]: ...

    async def get_new_marks(self) -> list[SubjectsBase]: ...
    async def get_new_marks_by_date(
        self, date: datetime, date_to: datetime | None = None, subject_id: str | None = None
    ) -> list[SubjectsBase]: ...

    async def get_marks_all(
        self, date: datetime | None = None, date_to: datetime | None = None, subject_id: str | None = None
    ) -> list[SubjectsBase]: ...

    async def format_all_marks(
        self, date: datetime | None = None, date_to: datetime | None = None, subject_id: str | None = None
    ) -> str: ...

    async def print_all_marks(
        self, date: datetime | None = None, date_to: datetime | None = None, subject_id: str | None = None
    ) -> None: ...
```

- `get_subjects()` — vrací seznam předmětů (každý `SubjectsBase` obsahuje vlastní `MarksRegistry`)
- `get_marks(subject_id)` — vrátí list známek (`MarksBase`) pro daný předmět
- `get_new_marks()` — vrací pouze nové známky (`is_new=True`) seskupené dle předmětů
- `get_new_marks_by_date(...)` — vrací nové známky v daném dni/rozsahu; volitelně pouze pro jeden předmět
- `get_marks_all(...)` — vrací všechny známky seskupené dle předmětů, s volitelnou filtrací
- `format_all_marks(...)` — vrátí formátovaný textový přehled
- `print_all_marks(...)` — vypíše přehled na standardní výstup
