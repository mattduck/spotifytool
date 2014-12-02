#-*- encoding: utf-8 -*-
import re
import sys
import argparse

import spotipy as spotify_web

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

        token_info = utils.get_spotify_web_oauth(namespace).get_cached_token()
        sp = spotify_web.Spotify(token_info["access_token"])

        # No need to look for a "starred" URI, as you can't get duplicates in
        # in the starred playlist.
        playlist_re = re.compile("spotify:user:%s:playlist:[\w]+" % config["USER"])
        given_playlist_uris = playlist_re.findall(input)

        all_playlists = {}
        user_playlists = sp.user_playlists(config["USER"])
        for playlist in user_playlists["items"]:
            all_playlists[playlist["uri"]] = playlist
        while user_playlists["next"]:
            user_playlists = sp._get(user_playlists["next"])
            for playlist in user_playlists["items"]:
                all_playlists[playlist["uri"]] = playlist

        chosen_playlists = []
        if is_exclude_mode:
            for playlist in all_playlists.itervalues():
                if playlist["uri"] in given_playlist_uris:
                    print "Excluding given playlist: %s" % playlist.name
                else:
                    chosen_playlists.append(playlist)
        else:
            for uri in given_playlist_uris:
                if uri in all_playlists:
                    chosen_playlists.append(all_playlists[uri])

        for playlist in chosen_playlists:
            self._process_playlist(playlist, sp, config, is_batch_mode)


    @classmethod
    def _process_playlist(self, playlist, sp, config, is_batch_mode, confirm=True):
        # The web API limits to 100 object deletions per request, but this
        # function handles larger lists automatically.
        #
        # I think we could implement this by manually calculating the offset of
        # track indexes to delete beyond the first 100, but it's easier and
        # more reliable to recursively process the whole playlist until
        # there are no duplicates left.
        def _print(msg):
            if confirm:
                print msg

        def _ask_to_include_playlist(name, count):
            if is_batch_mode or not confirm:
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


        _print("\nFinding duplicates for playlist: '%s'..." % playlist["name"])

        # Get all duplicate tracks for playlist
        playlist_track_uris = set()
        playlist_tracks_to_remove = {}

        # Tracks that don't have official spotify IDs (eg. local tracks)
        # can't be deleted.
        no_spotify_ids = []

        playlist_tracks = []
        tracks_result = sp._get(playlist["tracks"]["href"])
        for track in tracks_result["items"]:
            playlist_tracks.append(track["track"])
        while tracks_result["next"]:
            tracks_result = sp._get(tracks_result["next"])
            for track in tracks_result["items"]:
                playlist_tracks.append(track["track"])

        for i, track in enumerate(playlist_tracks):
            if not track["id"]:
                no_spotify_ids.append(i)
                continue
            
            if track["uri"] in playlist_track_uris:
                info = "    Duplicate found: index %d - %s - %s - %s - %s" % (
                        i,
                        " , ".join([t["name"] for t in track["artists"]]),
                        track["album"]["name"],
                        track["name"],
                        track["uri"])
                _print(info)
                if track["uri"] in playlist_tracks_to_remove:
                    playlist_tracks_to_remove[track["uri"]].append(i)
                else:
                    playlist_tracks_to_remove[track["uri"]] = [i]
                continue
            else:
                playlist_track_uris.add(track["uri"])

        msg_a = "    Can't process the below track indexes due to invalid Spotify ID:\n"
        msg_b = "        %s" % ", ".join([str(i) for i in no_spotify_ids])
        _print(msg_a + msg_b)

        remaining_dupes = 0
        for track_positions in playlist_tracks_to_remove.itervalues():
            remaining_dupes += len(track_positions)
        if remaining_dupes:
            if _ask_to_include_playlist(playlist["name"], remaining_dupes):
                _print("    Removing duplicates...")

                # Probably safer to use a snapshot ID
                playlist_snapshot_id = sp.user_playlist(
                    user=config["USER"],
                    playlist_id=playlist["id"],
                    fields=["snapshot_id"])["snapshot_id"]

                api_limit = 100
                tracks_to_remove = playlist_tracks_to_remove.items()[0:api_limit]
                tracks_obj = [{"uri": k, "positions": v} for k, v in tracks_to_remove]

                # Make the API call
                resp = sp.user_playlist_remove_specific_occurrences_of_tracks(
                    user=config["USER"], 
                    playlist_id=playlist["id"], 
                    tracks=tracks_obj,
                    snapshot_id=playlist_snapshot_id)

                # Process again if duplicates remain
                len_tracks_in_batch = 0
                for track in tracks_obj:
                    len_tracks_in_batch += len(track["positions"])

                remaining_dupes -= len_tracks_in_batch
                if remaining_dupes > 0:
                    self._process_playlist(playlist, sp, config, is_batch_mode, confirm=False)
        else:
            _print("    No duplicates found.\n")
