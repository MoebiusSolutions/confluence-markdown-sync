Confluence Markdown Sync
================

Overview
----------------

This Python script is used to push searchable content from a markdown
wiki to a Confluence wiki.

Caveats:

* The pages synced to Confluence are intended to populate search/browse indexes,
  and are not fully functional
    * Inter-page links are broken. Attachments are not synced.
    * Each page contains a link to it's real home (Bitbucket, etc) 
* The `README.md` content populates a root page
* All other pages are nested directly beneath it 
* All page creation/edits will notify anyone monitoring the Confluence space.
  I haven't figured out how to disable this.


Installation
----------------

### Setup the Scripts

Clone this repo:

```
git clone .../confluence-markdown-sync.git
cd confluence-markdown-sync/
```

Create/customize the page template file:

```
cp markdown-header.md.j2.example markdown-header.md.j2
```

... in particular, you'll want to modify this URL to point to your markdown repo:

```
...https://bitbucket.example.com/projects/MY_SPACE/repos/my-wiki/browse/...
```

Create/customize the config file:

```
cp config.json config.json.example
vi config.json
```

This file is affected by sections that follow.


### Setup Python

Install Python 3.6, if not already:

```
sudo yum install python36
```

Install PIP in the user's Python libs (`--user` recommended over `sudo`):

```
pip3 install --user pipenv
```

Install dependency libs:

```
# From this repo's directory
cd confluence-markdown-sync
pipenv install
```

Launch a shell with the pipenv active:

```
pipenv shell
```

### Prepare the Markdown Source

Clone your markdown repo:

```
git clone .../my-wiki.git
```

Modify your `config.json` to point at this directory.


### Run the Scripts

Execute the sync process:

```
# From this repo's directory
cd confluence-markdown-sync

pipenv run python main.py --config config.json
```

