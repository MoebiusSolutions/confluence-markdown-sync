Release Notes
================

0.2 (IN-DEVELOPMENT)
----------------

* Replaced calls to "acli" (Bob Swift command line tool) with the
  "atlassian-python-api" python library, which requires no plugins to the Confluence server
* Rolled python version from 3.6 to 3.8
* Added `root_page_title` configuration option, which is necessary with the new API calls
* Added token authentication to the config file
* Separated `markdown_dir` and `state_dir` configuraion options
* Added [Release-Notes.md](Release-Notes.md)


0.1 (2020-07-02)
----------------

* Initial Release
