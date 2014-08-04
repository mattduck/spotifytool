#-*- encoding: utf-8 -*-
import re
import sys
import argparse

import command
import utils

def _get_track_info_str(spotify_track):
    return "%s  -  %s  -  %s  -  %s" % (
        spotify_track.artists[0].load().name.encode("utf-8"),
        spotify_track.album.load().name.encode("utf-8"),
        spotify_track.name.encode("utf-8"),
        str(spotify_track.link),
        )


class Uniq(command.Command):

    description="Parse standard input for Spotify playlist URIs, and "\
    "remove duplicate tracks from those playlists"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool uniq",
            description=self.description,
        )

        parser.add_argument("--exclude-stream",
            help="Inverse behaviour - remove duplicate tracks from all your playlists "\
            "except those parsed from standard input",
            action="store_true",
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
        is_exclude_mode = namespace.exclude_stream
        config = utils.read_config(namespace)

        def _ask_to_include_playlist(name, count):
            if is_batch_mode:
                    return True

            choices = { "y": True, "yes": True, "n": False, "no": False }

            # The default interactive choice is to /not/ remove
            default_choice = False
            msg = 'Remove %d duplicate tracks from playlist "%s" [y/N]? '

            while True:
                response = raw_input(msg % (count, name))
                if response in choices:
                    return choices[response]
                elif response == "":
                    return default_choice
                else:
                    print "Please respond with 'y' or 'n', or leave blank for default value."

        session = utils.get_spotify_lib_session(namespace)

        # No need to look for a "starred" URI, as you can't get duplicates in
        # in the starred playlist.
        playlist_re = re.compile("spotify:user:%s:playlist:[\w]+" % config["USER"])
        playlist_uris = playlist_re.findall(input)

        chosen_playlists = []
        if is_exclude_mode:
            for playlist in session.playlist_container.load():
                if str(playlist.load().link) in playlist_uris:
                    print "Excluding given playlist: %s" % playlist.name
                else:
                    chosen_playlists.append(playlist)
        else:
            for uri in playlist_uris:
                playlist = session.get_playlist(uri).load()
                chosen_playlists.append(playlist)

        for playlist in chosen_playlists:

            print "Finding duplicates for playlist: '%s'..." % playlist.name

            # Get all duplicate tracks for playlist
            playlist_track_links = set()
            playlist_indexes_to_remove = []
            for i, this_track in enumerate(playlist.tracks):
                try:
                    this_track = this_track.load()
                except Exception:
                    print "   Exception for index %d" % i
                    continue

                this_track_link = str(this_track.link)
                if this_track_link in playlist_track_links:
                    print "    Duplicate found:  Track %d  -  %s" % (
                        i + 1, _get_track_info_str(this_track))
                    playlist_indexes_to_remove.append(i)
                    continue
                else:
                    playlist_track_links.add(this_track_link)

            # Remove the duplicate tracks, if desired
            num_of_duplicates = len(playlist_indexes_to_remove)
            if num_of_duplicates:
                if _ask_to_include_playlist(playlist.name, num_of_duplicates):
                    print "    Removing duplicates..."
                    playlist.remove_tracks(playlist_indexes_to_remove)
                    print "    ...done.\n"
            else:
                print "    No duplicates found.\n"
