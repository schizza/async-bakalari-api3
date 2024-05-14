[![codecov](https://codecov.io/gh/schizza/async-bakalari-api3/graph/badge.svg?token=KC2WYAOLOP)](https://codecov.io/gh/schizza/async-bakalari-api3)

Dokumentace k dispozici [zde](https://async-bakalari-api.schizza.cz)

# Python async client for Bakalari API v3

## 0.0.2

## Added

* better exceptions handling and logging
* class Komens
  * count unread messages
  * get all messages

* tests and coverage

## Changed

* async_schools_list moved to Bakalari class
* Refactor login functions
* Refactor token handling

## Fixed

* Invalid refresh token
* Refactor send_request to better maintenance

### v0.1

## Class School from `datastructure.py`

Now supports to download list of schools with their API points.

* get_url by school name or index in list
* search school by town
* cache list of schools by saving and loading list in JSON format

## Class Bakalari

* first login with username and password and stores access and refresh token
* automaticaly refreshes access token with refresh token if refresh token is not expired
* save access and refresh token localy to be cached

## Class Komens

* count unread messages `count_unread_messages`
