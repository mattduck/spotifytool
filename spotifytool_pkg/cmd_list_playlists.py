import sys
import argparse
import re

import spotipy as spotify_web

import command
import utils

class ListPlaylists(command.Command):

    description="Parse standard input for Spotify URIs and output "\
    "all child playlist URIs"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool list-playlists",
            description=self.description
        )

        parser.add_argument("--user",
            action="store_true",
            help="For each user URI, output all of that user's playlist URIs",
        )

        parser.add_argument("--playlist",
            action="store_true",
            help="Output incoming playlist URIs",
        )

        self._add_config_arg_to_parser(parser)

        return parser.parse_args(args)

    @classmethod
    def run(self, namespace):
        input = sys.stdin.read()

        token_info = utils.get_spotify_web_oauth(namespace).get_cached_token()
        sp = spotify_web.Spotify(token_info["access_token"])

        ALL_PLAYLISTS = []

        if namespace.user:
            user_re = re.compile("spotify:user:[\w]+")
            for user_uri in user_re.findall(input):
                user_id = user_uri.split(":")[2]

                user_playlists = sp.user_playlists(user_id)
                for playlist in user_playlists["items"]:
                    ALL_PLAYLISTS.append(playlist)
                while user_playlists["next"]:
                    user_playlists = sp._get(user_playlists["next"])
                    for playlist in user_playlists["items"]:
                        ALL_PLAYLISTS.append(playlist)

        if namespace.playlist:
            playlist_re = re.compile("spotify:user:[\w]+:playlist:[\w]+")
            for playlist_uri in playlist_re.findall(input):
                # Don't need to call API, as we're just outputting the
                # track_uri directly
                playlist = {"uri": playlist_uri}
                ALL_PLAYLISTS.append(playlist)

        for playlist in ALL_PLAYLISTS:
            print playlist["uri"]
