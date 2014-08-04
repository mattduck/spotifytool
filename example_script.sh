#!/bin/bash

# Some examples / tests. 
# WARNING - this will edit your Spotify playlists and library! 

# Swap these values for your own
USER=spotify:user:mattduck
TEST_PLAYLIST=spotify:user:mattduck:playlist:7c2iCz9BY3SNrsdR0I9LjY

set -e
shopt -s expand_aliases
alias sp="spotifytool"

echo "Authenticate the web API..."
sp weblogin
echo "========================================================================="

echo "Backup all playlists to directory as CSV files..."
sp backup "example_backup"
echo "========================================================================="

echo "Parse a file for track URIs and add them to a playlist..."
cat "example_backup/spotify_starred - default.csv" | sp write-playlist "$TEST_PLAYLIST" --batch
echo "========================================================================="

echo "Remove duplicates from all your playlists, interactively..."
echo "" | sp uniq --exclude-stream
echo "========================================================================="

echo "List all track URIs for a given album URI..."
album_uri=spotify:album:3luXaBPCDQ0BwX3PmBimqr # Benjamin Shaw - Goodbye, Cagoule World
echo "$album_uri" | sp list-tracks --album
echo "========================================================================="

echo "Append those tracks to a playlist interactively..."
echo "$album_uri" | sp list-tracks --album | sp write-playlist "$TEST_PLAYLIST"
echo "========================================================================="

echo "Add all tracks by an artist to your library without confirmation..."
artist=spotify:artist:2ApaG60P4r0yhBoDCGD8YG # Elliott Smith
echo "$artist" | sp list-tracks --artist | sp write-library --batch
echo "========================================================================="

echo "List all playlists by a user..."
echo "$USER" | sp list-playlists --user
echo "========================================================================="
