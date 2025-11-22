## Rychlá referenční API

``` py linenums="1" title="Hlavní metody"
class Marks:
    async def fetch_marks(self) -> None: ...
    async def get_subjects(self) -> list[SubjectsBase]: ...
    async def get_marks_by_subject(self, subject_id: str) -> list[MarksBase]: ...

    async def get_new_marks(self) -> list[SubjectsBase]: ...
    async def get_new_marks_by_date(
        self, date_from: datetime, date_to: datetime, subject_id: str | None = None
    ) -> list[SubjectsBase]: ...

    async def get_marks_all(
        self, date_from: datetime | None = None, date_to: datetime | None = None, subject_id: str | None = None
    ) -> list[SubjectsBase]: ...

    async def format_all_marks(
        self, date_from: datetime | None = None, date_to: datetime | None = None, subject_id: str | None = None
    ) -> str: ...

    async def get_flat(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        order: Literal["asc", "desc"] = "desc",
        predicate: Callable[[MarksBase], bool] | None = None,
    ) -> list[FlatMark]: ...

    async def get_snapshot(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        order: Literal["asc", "desc"] = "desc",
        predicate: Callable[[MarksBase], bool] | None = None,
        to_dict: bool = True,
    ) -> FlatSnapshot | dict[str, Any]: ...

    async def get_snapshot_for_school_year(
        self,
        *,
        school_year: tuple[datetime, datetime],
        order: Literal["asc", "desc"] = "desc",
    ) -> FlatSnapshot | dict[str, Any]: ...

    async def diff_ids(
        self,
        previous_ids: set[str],
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        subject_id: str | None = None,
        predicate: Callable[[MarksBase], bool] | None = None,
    ) -> tuple[set[str], list[FlatMark]]: ...

    async def get_all_marks_summary(self) -> dict[str, str]: ...
```

- `get_subjects()` — vrací seznam předmětů (každý `SubjectsBase` obsahuje vlastní `MarksRegistry`)
- `get_marks_by_subject(subject_id)` — vrátí list známek (`MarksBase`) pro daný předmět
- `get_new_marks()` — vrací pouze nové známky (`is_new=True`) seskupené dle předmětů
- `get_new_marks_by_date(date_from, date_to, subject_id=None)` — vrací nové známky v daném dni/rozsahu; volitelně pouze pro jeden předmět
- `get_marks_all(date_from=None, date_to=None, subject_id=None)` — vrací všechny známky seskupené dle předmětů, s volitelnou filtrací
- `format_all_marks(date_from=None, date_to=None, subject_id=None)` — vrátí formátovaný textový přehled
- `get_flat(...)` — vrátí zploštělý seznam známek (`FlatMark`) s metadaty předmětů; podporuje řazení a predikát
- `get_snapshot(...)` — vrátí kompaktní snímek dat: `subjects`, `marks_grouped`, `marks_flat`
- `get_snapshot_for_school_year(school_year, order="desc")` — vytvoří snapshot za zadaný školní rok (od-do)
- `diff_ids(previous_ids, ...)` — porovná ID známek s předchozí sadou a vrátí nová ID spolu s novými položkami
- `get_all_marks_summary()` — vrátí agregovaný souhrn napříč všemi předměty
