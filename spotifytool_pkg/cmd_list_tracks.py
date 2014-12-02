import sys
import argparse
import re

import spotipy as spotify_web

import command
import utils

class ListTracks(command.Command):

    description="Parse standard input for Spotify URIs and output "\
    "all child track URIs"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool list-tracks",
            description=self.description,
        )

        parser.add_argument("--user",
            action="store_true",
            help="For each user URI, output all of that user's playlists' track URIs",
        )

        parser.add_argument("--playlist",
            action="store_true",
            help="For each playlist URI, output all of that playlist's track URIs",
        )

        parser.add_argument("--artist",
            action="store_true",
            help="For each artist URI, output all of that artist's albums' track URIs",
        )

        parser.add_argument("--album",
            action="store_true",
            help="For each album URI, output all of that album's track URIs",
        )

        parser.add_argument("--track",
            action="store_true",
            help="Output incoming track URIs",
        )

        self._add_config_arg_to_parser(parser)
        return parser.parse_args(args)

    @classmethod
    def run(self, namespace):
        input = sys.stdin.read()
        config = utils.read_config(namespace)

        token_info = utils.get_spotify_web_oauth(namespace).get_cached_token()
        sp = spotify_web.Spotify(token_info["access_token"])

        ALL_TRACKS = []

        if namespace.user:
            user_re = re.compile("spotify:user:[\w]+")
            for user_uri in user_re.findall(input):
                user_id = user_uri.split(":")[2]

                playlists_full_res = []
                playlists_result = sp.user_playlists(user_id)
                for playlist in playlists_result["items"]:
                    playlists_full_res.append(playlist)

                while playlists_result["next"]:
                    playlists_result = sp._get(playlists_result["next"])
                    for playlist in playlists_result["items"]:
                        playlists_full_res.append(playlist)

                for playlist in playlists_full_res:

                    # Get all track results from API
                    tracks_result = sp._get(playlist["tracks"]["href"])
                    for track in tracks_result["items"]:
                        ALL_TRACKS.append(track)
                    while tracks_result["next"]:
                        tracks_result = sp._get(tracks_result["next"])
                        for track in tracks_result["items"]:
                            ALL_TRACKS.append(track)


        if namespace.playlist:
            playlist_re = re.compile("spotify:user:[\w]+:playlist:[\w]+")
            for playlist_uri in playlist_re.findall(input):

                segments = playlist_uri.split(":")
                user_id = segments[2]
                playlist_id = segments[4]

                playlist = sp.user_playlist(user_id, playlist_id)

                # Get all track results from API
                tracks_result = sp._get(playlist["tracks"]["href"])
                for track in tracks_result["items"]:
                    ALL_TRACKS.append(track)
                while tracks_result["next"]:
                    tracks_result = sp._get(tracks_result["next"])
                    for track in tracks_result["items"]:
                        ALL_TRACKS.append(track)

        if namespace.artist:
            artist_re = re.compile("spotify:artist:[\w]+")
            for artist_uri in artist_re.findall(input):
                artist_id = artist_uri.split(":")[2]

                # Get all artist albums
                all_album_hrefs = []
                artist_albums = sp.artist_albums(
                        artist_id, 
                        album_type="album,compilation", # No singles / appears_on
                        country=config["COUNTRY"],
                        limit=50,
                        )
                for album in artist_albums["items"]:
                    all_album_hrefs.append(album["href"])
                while artist_albums["next"]:
                    artist_albums = sp._get(artist_albums["next"])
                    for album in artist_albums["items"]:
                        all_album_hrefs.append(album["href"])

                # Get all album tracks
                for href in all_album_hrefs:
                    album = sp._get(href)
                    album_tracks = album["tracks"]
                    for track in album_tracks["items"]:
                        ALL_TRACKS.append(track)
                    while album_tracks["next"]:
                        album_tracks = sp._get(album_tracks["next"])
                        for track in album_tracks["items"]:
                            ALL_TRACKS.append(track)


        if namespace.album:
            album_re = re.compile("spotify:album:[\w]+")
            for album_uri in album_re.findall(input):
                album_id = album_uri.split(":")[2]
                album = sp.album(album_id)

                album_tracks = album["tracks"]
                for track in album_tracks["items"]:
                    ALL_TRACKS.append(track)
                while album_tracks["next"]:
                    album_tracks = sp._get(album_tracks["next"])
                    for track in album_tracks["items"]:
                        ALL_TRACKS.append(track)


        if namespace.track:
            track_re = re.compile("spotify:track:[\w]+")
            for track_uri in track_re.findall(input):
                # Don't need to call API, as we're just outputting the
                # track_uri directly
                track = {"uri": track_uri}
                ALL_TRACKS.append(track)

        for track in ALL_TRACKS:
            # ALL_TRACKS contains both playlist track objects and normal track
            # objects
            if "track" in track:
                print track["track"]["uri"]
            else:
                print track["uri"]
