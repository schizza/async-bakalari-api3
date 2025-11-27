# Changelog

All notable changes to this project will be documented in this file.

🇨🇿 Full documentation (czech) on [this site](https://async-bakalari-api.schizza.cz)

## 0.8.1

## 🧹 Refaktoring / Údržba

- bump version to 0.8.1

## 0.8.0

## ✨ Nové funkce

- **Add confirmed field to marks and support unconfirmed marks** (#154) @schizza
  
  - Přidán atribut `confirmed` pro známky
  - umožňuje sledovat stav potvrztení známky na serveru
  - přidána funkce `get_unconfirmed_marks() -> list[SubjectBase]`, která vrací pouze nepotvrzené známky.
  
 - **Add mark message as read and get_single_message** (#147) @schizza
  
  - Přidána funkce `message_mark_read(message_id: str)`, která označí zprávu za přečtenou
  - Přidána funkce ` message_get_single_message(message_id: str`), která vratí aktualizovanou zprávu s `message_id`
  
## 0.7.0

## ✨ Nové funkce

- **Adds marks summary function** (#141) @schizza

  Přidána funkce `get_all_marks_summary`, která vrací sumarizovaný přehled o známkách a předmětech. 
  Vrací `průměr` počítaný z průměru předmětů, `vážený průměr` počítaný ze všech znmek, `počet předmětů`, `počet celkových známek`, `počet numerických známek` a `počet bodovaných známek`

## 🐛 Opravy chyb

- **Limits the number of authentication retries** (#143) @schizza
  Přidává limit pro opakování při chybné authentizaci.
  Zabraňuje nekonečné smyčce při chybném tokenu.

## 🧹 Refaktoring / Údržba

- **Add asynchronous context manager and close method** (#133) @schizza

  Zavádí asynchronní kontextový manažer pro správu životního cyklu klientské session, který zajišťuje správné uvolňování prostředků, a přidává explicitní metodu pro ukončení.

- Refakorizace logování tak, aby využívalo modul logging ze standardní knihovny místo vlastní implementace.

- **Make school list save/load async** (#144) @schizza
  Oprava ukládání a načítání seznamu škol ze souboru, tak aby využívala asynchronní metody.
  Fixes #116

- Přidány testy k novým modalitám, oprava testů u refaktorovaných modalit.

## 0.6.0

### Adds

- Adds marks helpers for data manipulation, including flat mark
representation and snapshot creation, grouping.
- Implements session handling and refresh token logic to ensure thread
safety.

This change introduces:
- `FlatMark` dataclass for a simplified mark representation.
- Functions to convert between `MarksBase` and `FlatMark`.
- Methods for iterating over grouped marks.
- A `get_snapshot` method to create a structured snapshot of marks data.

### Refactor
Refactors and improves API client (#129)
- Upgrades Python version to 3.13 in CI and `pyproject.toml`
- Applies minor formatting changes
- Implements more robust error handling and data validation.


### Tests
- Adds tests to cover various error branches and edge cases
in Bakalari and Komens modules, increasing overall test
coverage and robustness.



## [0.5.0]

### Adds
 - New `Timetable` module introduced
   - This commit introduces the ability to fetch and parse timetable data from the Bakalari API, including actual and permanent timetables. It also defines data structures for representing timetable entities like lessons, changes, and other related information.

## [0.4.0]

### Breaking Changes
 - `Credentials` are now required to be passed to `Bakalari` constructor as they are set to read-only properties.
 - Renamed `src/bakalari_api` to `src/async_bakalari_api` for consistency

### Changed
 - Introducing a lock to handle concurrent refresh token requests, preventing race conditions.
 - Ensuring each Bakalari instance has its own dedicated credentials and session, preventing credential sharing between instances.
 - Strip requirements to minimum
 - Updated wheel build

 ### Fixed
 - Using a context manager to properly manage the aiohttp session.


## [0.3.8]

### Fixed
 - `Credentials` in `Bakalari` is instance, not reference to credentials. This fixes issue with multiple instances of `Bakalari` sharing the same credentials.


 ## [0.3.7]

### Fixed
 - `await` keyword was missing in the code snippet

### Changed
 - Renamed `src/bakalari_api` to `src/async_bakalari_api` for consistency
 - Strip requirements to minimum
 - Updated wheel build

## 0.3.4 - 0.3.6
  - Minor bugfixes, version bumps for Home Assistant

## [0.3.3]

### Added
- New module `Marks` to handle marks from server
  - Adds endpoint to retrieve marks.

### Changed
- Added logging for file operations
- Refactored API logger initialization
- Argument parsing for CLI appliaction - now `auto_cache` option is available with `-cf` option
- Fix proper session closure on deletion

[0.3.2]

### Added

- class `Schools()` is accessible by `Bakalari` class in `self.schools`
- `Schools` now support operations with towns
- new data structure `UniqueTowns` that hold all town names
  - `get_town_partial_name` returns list of the towns based on partial name
  - `get_all_towns` returns list of all towns
  - `istown` checks if the town is present in the list
  - `count_towns` returns number of towns in list

### Changed

- automatically load credentials if auto_cache is on
- recursive search in towns when fetching `schools_list` from server. Recursive search is enabled by default. You can turn it off by `school_list(... , recursive=False)`

## [0.3.1]

### Added

- `Schools` now support operations with towns
- new data structure `UniqueTowns` that hold all town names
  - `get_town_partial_name` returns list of the towns based on partial name
  - `get_all_towns` returns list of all towns
  - `istown` checks if the town is present in the list
  - `count_towns` returns number of towns in list

## Changed

- dependency list is divided to application dependencies and development dependencies
- if `auto_cache_credentials` and `cache_filename` is set then credentials are loaded automatically

## [0.3]

### Added

- `bakalari_demo.py` is now CLI application
- `Komens` now support for downloading attachment - `get_attachment`
- `send_auth_request` now supports extending EndPoints url wiht `extend` argument
- `school_list` now supports variable `town` - fetch schools in the town to limit downloading full list of schools.
- `Messages` class now have function `json` to return messages as JSON representative
- `Messages` class have `__str__` function for better handling `str(Messages)`

### Changed

- refactor of the code for speed and better reading of the code
- `school_list` now fetching schools in concurency mode - improved speed form about 1:30 min to 20s
- `mid` variable in the `MessageContainter` is now string instead of integer.
- `async_school_list` renamed to `school_list` as all methods are async
- `MessageContainter` returns JSON bytes on `as_json()` call instead of `orjson.Fragment`
- `get_messsages()` renamed to `fetch_messages()`

### Removed

- `username` from `Credentials` - as we do not need to store it

## [0.2]

### Added

- better exceptions handling and logging
- `class Komens`
  - count unread messages
  - get all messages
  - tests and coverage

### Changed

- `async_schools_list` moved to `Bakalari` class
- Refactor login functions
- Refactor token handling

### Fixed

- Invalid refresh token
- Refactor send_request to better maintenance

## [0.0.1]

### Added

- main `class Bakalari`

  - supports saving `access token` and `refresh token` localy
  - automatically refreshes access token with refresh token if refresh token is not expired

- `class Schools` in `datastructures.py` lists all schools with their API points

  - get_url by school name or index in list
  - search school by town
  - cache list of schools by saving and loading list in JSON format

[unreleased]: https://github.com/schizza/bakalari-api3/compare/v0.0.1...HEAD
[0.4.0]: https://github.com/schizza/bakalari-api3/releases/tag/0.4.0
[0.3.8]: https://github.com/schizza/bakalari-api3/releases/tag/0.3.8
[0.3.7]: https://github.com/schizza/bakalari-api3/releases/tag/0.3.7
[0.3.3]: https://github.com/schizza/bakalari-api3/releases/tag/0.3.3
[0.3.2]: https://github.com/schizza/bakalari-api3/releases/tag/0.3.2
[0.3.1]: https://github.com/schizza/bakalari-api3/releases/tag/0.3.1
[0.3]: https://github.com/schizza/bakalari-api3/releases/tag/0.3
[0.2]: https://github.com/schizza/bakalari-api3/releases/tag/0.2
[0.0.1]: https://github.com/schizza/bakalari-api3/releases/tag/v0.0.1
