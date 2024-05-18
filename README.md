[![codecov](https://codecov.io/gh/schizza/async-bakalari-api3/graph/badge.svg?token=KC2WYAOLOP)](https://codecov.io/gh/schizza/async-bakalari-api3)

# Changelog

All notable changes to this project will be documented in this file.

🇨🇿 Full documentation (czech) on [this site](https://async-bakalari-api.schizza.cz)

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
[0.0.1]: https://github.com/schizza/bakalari-api3/releases/tag/v0.0.1
