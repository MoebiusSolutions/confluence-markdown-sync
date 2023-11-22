Confluence Markdown Sync
================

Overview
----------------

This Python script is used to push searchable content from a markdown
wiki to a Confluence wiki.

Caveats/Features:

* The pages synced to Confluence are intended for searching/browsing,
  but they are too ugly for to be the primary viewing interface
  and are not fully functional
    * Each page contains a link to it's real home (Bitbucket, etc)
      for proper viewing
* The `README.md` content populates a the root Confluence page,
    * All other pages are nested directly beneath it 
* All page creation/edits may notify anyone monitoring the Confluence space,
  so be mindful about spam


Build the Docker Image
----------------

Clone this repo:

    git clone https://github.com/MoebiusSolutions/confluence-markdown-sync.git
    cd confluence-markdown-sync/

Build the docker image:

    sudo docker build --tag confluence-markdown-sync:local-build .


Configuration
----------------

Create/customize the config file:

    cp config.json.example config.json

Create/customize the page template file:

    cp page-template.j2.example page-template.j2

... in particular, you'll want to modify this URL to point to your markdown repo
(in Bitbucket or wherever):

    ...https://bitbucket.example.com/projects/MY_SPACE/repos/my-wiki/browse/...

You can look at the raw syntax of any existing Confluence page
with the **View Storage Format** option in the page menu.
This should help you craft your own template.
Note that the rendered Markdown content comes out as vanilla HTML.


Execution
----------------

Execute the sync process:

    # From this repo's directory
    cd confluence-markdown-sync

    sudo docker run --rm -it \
        -u "$(id -u):$(id -g)" \
        --security-opt label=disable \
        -v "$PWD/page-template.j2:/page-template.j2:ro" \
        -v "$PWD/config.json:/config.json:ro" \
        -v "$HOME/my-wiki:/wiki-markdown:ro" \
        -v "$HOME/my-wiki-state:/wiki-state:rw" \
        confluence-markdown-sync:local-build --config /config.json

... where:

* `-u "$(id -u):$(id -g)"`:
  It is generally helpful to run as the host user/group when mounting
  directories from the host.

* `--security-opt label=disable`:
  This avoids permissions issues that can come from SELinux when using
  mounts from the host.

Other Notes
----------------

[Release Notes](Release-Notes.md)
