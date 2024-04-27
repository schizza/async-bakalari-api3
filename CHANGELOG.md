# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- better excetions handling and logging
- `class Komens`
  - count unread messages

### Fixed
  
- Invalid refresh token

## [0.0.1]

### Added

- main `class Bakalari`

  - supports saving `access token` and `refresh token` localy
  - automaticaly refreshes access token with refresh token if refresh token is not expired
  
- `class Schools` in `datastructures.py` lists all schools with their API points
  
  - get_url by school name or index in list
  - search school by town
  - cache list of schools by saving and loading list in JSON format

[unreleased]: https://github.com/schizza/bakalari-api3/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/schizza/bakalari-api3/releases/tag/v0.0.1
