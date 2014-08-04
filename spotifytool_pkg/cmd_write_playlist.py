#-*- encoding: utf-8 -*-
import sys
import argparse
import re

import spotipy as spotify_web

import command
import utils

class WritePlaylist(command.Command):

    description="Parse standard input for Spotify track URIs and add "\
    "them to a playlist. Playlist must exist"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool write-playlist",
            description=self.description,
        )

        parser.add_argument("playlist_id",
            help="Playlist URI to add tracks to",
            metavar="playlist-id",
        )

        parser.add_argument("--batch",
            help="Non-interactive mode",
            action="store_true",
        )

        self._add_config_arg_to_parser(parser)
        return parser.parse_args(args)

    @classmethod
    def run(self, namespace):

        # Want to read input from stdin, and then have raw_input prompt the
        # user, ignoring everything from the original stdin input.
        input = sys.stdin.read()
        sys.stdin = open("/dev/tty")

        is_batch_mode = namespace.batch
        config = utils.read_config(namespace)

        url_segment = "spotify:user:%s:playlist:" % config["USER"]
        playlist_id = namespace.playlist_id.strip(url_segment)

        def _ask_to_include_track(playlist, track):
            if is_batch_mode:
                return True

            choices = { "y": True, "yes": True, "n": False, "no": False }

            default_choice = False
            msg = "Add track to playlist '%s': %s - %s - %s [y/N]? "
            full_msg = msg % (
                playlist["name"],
                track["artists"][0]["name"],
                track["album"]["name"],
                track["name"],
            )

            while True:
                response = raw_input(full_msg)
                if response in choices:
                    return choices[response]
                elif response == "":
                    return default_choice
                else:
                    print "Please respond with 'y' or 'n', or leave blank for default value."

        
        token_info = utils.get_spotify_web_oauth(namespace).get_cached_token()
        sp = spotify_web.Spotify(token_info["access_token"])

        playlist = sp.user_playlist(config["USER"], playlist_id)

        track_re = re.compile("spotify:track:[\w]+")
        track_uris = track_re.findall(input)

        if is_batch_mode:
            track_uris_to_include = track_uris
        else:
            track_uris_to_include = []
            for track_uri in track_uris:
                track = sp.track(track_uri)
                if _ask_to_include_track(playlist, track):
                    track_uris_to_include.append(track_uri)


        msg = "Number of tracks to add to playlist '%s': '%d'"
        print msg % (playlist["name"], len(track_uris_to_include))
        print "Making web API calls..."

        # You can submit multiple tracks at once, but I think if one URI is
        # bad, the whole call might fail, so just do one at a time for now.
        for uri in track_uris_to_include:
            try:
                print "Adding uri: %s..." % uri
                json_uri = [uri] # Spotipy converts the object to json
                sp.user_playlist_add_tracks(config["USER"], playlist_id, json_uri)
                print "  done."
            except spotify_web.SpotifyException:
                print "  Bad return value."
