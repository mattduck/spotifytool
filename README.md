# spotifytool

A CLI that I'm using to manage my Spotify data. It's not polished, but somebody
might find it useful.

- Github: [https://github.com/mattduck/spotifytool](https://github.com/mattduck/spotifytool)

## Commands

For full command help, run `spotifytool --help`, or `spotifytool <command>
--help`. 

- __backup__: Backup all Spotify playlists as CSV files.

- __list-playlists__: Parse standard input for Spotify URIs and output all child
  playlist URIs.

- __list-tracks__: Parse standard input for Spotify URIs and output all child
  track URIs.

- __uniq__: Parse standard input for Spotify playlist URIs, and remove duplicate
  tracks from those playlists.

- __weblogin__: Store user login details, to be used by the Spotify web API.

- __write-library__: Parse standard input for Spotify track URIs and add them to
  your track library.

- __write-playlist__: Parse standard input for Spotify track URIs and add them
  to a playlist. Playlist must exist.

Some example / test commands are in [example_script.sh](https://github.com/mattduck/spotifytool/blob/master/example_script.sh).
Quick examples below:

``` bash
# Backup your playlists and library as CSV files:
spotifytool backup "$DIRECTORY"

# Parse files for track URIs, and add them to a playlist:
cat "$FILE" "$FILE" | spotifytool write-playlist "$PLAYLIST_URI"

# Remove duplicate tracks from given playlists:
echo "$PLAYLIST_URIS" | spotifytool uniq

# List all track URIs belonging to given artists, and add those tracks to your
# library: 
echo "$ARTIST_URIs" | spotifytool list-tracks --artist | spotifytool write-library --batch

# List all tracks belonging to playlists of particular users, and add those to a
# playlist:
echo "$USER_URIs" | spotifytool list-tracks --user | spotifytool write-playlist "$PLAYLIST_URI"
```

## Installation

Requires [spotipy](https://github.com/plamere/spotipy) (Web API client).

`python setup.py install` will install the `spotifytool` script, along with the
`spotifytool_pkg` Python library.


## Configuration

Some configuration is required - API details, account details. The program
expects to find a default config file at `~/.spotifytoolconfig`, or for a path to
the config file to be given with the `--config` argument.

The expected config format can be seen in [example_config.ini](https://github.com/mattduck/spotifytool/blob/master/example_config.ini).


## APIs

- Spotifytool uses the Spotify Web API, which requires an API key to access user
  data. This can be requested at [https://developer.spotify.com](https://developer.spotify.com).

- I used to use libspotify too, but removed it when the web API had enough features.
