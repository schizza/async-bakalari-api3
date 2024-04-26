# Python async client for Bakalari API v3

Initial version.

## Class School from `datastructure.py`

Now supports to download list of schools with their API points.

* get_url by school name or index in list
* search school by town
* cache list of schools by saving and loading list in JSON format

## Class Bakalari

* first login with username and password and stores access and refresh token
* automaticaly refreshes access token with refresh token if refresh token is not expired
* save access and refresh token localy to be cached
