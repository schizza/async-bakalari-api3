# Changelog

All notable changes to this project will be documented in this file.

🇨🇿 Full documentation (czech) on [this site](https://async-bakalari-api.schizza.cz)

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
[0.3.2]: https://https://github.com/schizza/bakalari-api3/releases/tag/0.3.2
[0.3.1]: https://https://github.com/schizza/bakalari-api3/releases/tag/0.3.1
[0.3]: https://https://github.com/schizza/bakalari-api3/releases/tag/0.3
[0.2]: https://github.com/schizza/bakalari-api3/releases/tag/0.2
[0.0.1]: https://github.com/schizza/bakalari-api3/releases/tag/v0.0.1
