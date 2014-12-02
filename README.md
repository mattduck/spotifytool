# spotifytool

A CLI that I'm using to manage my Spotify data. It's not polished, but somebody
might find it useful.


## Examples

For full command help, run `spotifytool --help`, or `spotifytool <command>
--help`. Some example / test commands are in `example_script.sh`.

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

The expected config format can be seen in `example_config.ini`.


## APIs

- Spotifytool uses the Spotify Web API, which requires an API key to access user
  data. This can be requested at [https://developer.spotify.com](https://developer.spotify.com).

- I used to use libspotify too, but removed it when the web API had enough features.
