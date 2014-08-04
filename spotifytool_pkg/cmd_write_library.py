import sys
import argparse
import re

import spotipy as spotify_web

import command
import utils

class WriteLibrary(command.Command):

    description="Parse standard input for Spotify track URIs and add "\
    "them to your track library"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool write-library",
            description=self.description,
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

        def _ask_to_include_track(track):
            if is_batch_mode:
                return True

            choices = { "y": True, "yes": True, "n": False, "no": False }

            default_choice = True
            msg = "Add track to library: %s - %s - %s [y/N]? "
            full_msg = msg % (
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

        track_re = re.compile("spotify:track:[\w]+")
        track_uris = track_re.findall(input)

        if is_batch_mode:
            track_uris_to_include = track_uris
        else:
            track_uris_to_include = []
            for track_uri in track_uris:
                track = sp.track(track_uri)
                if _ask_to_include_track(track):
                    track_uris_to_include.append(track_uri)


        print "Number of tracks to add to library: '%d'" % len(track_uris_to_include)
        print "Making web API calls..."

        # You can submit multiple tracks at once, but I think if one URI is
        # bad, the whole call might fail, so just do one at a time for now.
        for uri in track_uris_to_include:
            try:
                print "Adding uri: %s..." % uri
                sp.current_user_saved_tracks_add([uri])
                print "  done."
            except spotify_web.SpotifyException:
                print "  Bad return value."

