# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

- download Komens attachment
- `send_auth_request` now support extending EndPoints wiht `extend` argument

### Changed

- `mid` in `MessageContainter` is now string instead of integer.

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
