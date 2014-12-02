#-*- coding: utf-8 -*-
import os
import argparse
import csv

import spotipy as spotify_web

import command
import utils


class Backup(command.Command):

    description="Backup all Spotify playlists as CSV files"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool backup",
            description=self.description,
        )

        parser.add_argument("dir",
            help="Destination directory for CSV files",
            metavar="backup_dir",
        )

        self._add_config_arg_to_parser(parser)
        return parser.parse_args(args)

    @classmethod
    def run(self, namespace):
        config = utils.read_config(namespace)

        print "Backing up user playlists, starred and library..."

        backup_dir = namespace.dir
        if backup_dir.endswith("/"):
            backup_dir = backup_dir[:-1]
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        token_info = utils.get_spotify_web_oauth(namespace).get_cached_token()
        sp = spotify_web.Spotify(token_info["access_token"])

        # Want to backup multiple collections of tracks:
        # - All playlists
        # - The old "starred" playlist / collection
        # - The new user track library

        # Items are in format (name, id, href_to_tracks_endpoint)
        all_collections = [
            ("spotify_starred", "default", "users/%s/starred/tracks" % config["USER"]),
            ("spotify_library", "default", "me/tracks"),
        ]

        # Get all playlists - this might require multiple calls.
        playlists_full_res = []
        playlists_result = sp.user_playlists(config["USER"])
        for playlist in playlists_result["items"]:
            playlists_full_res.append(playlist)

        while playlists_result["next"]:
            playlists_result = sp._get(playlists_result["next"])
            for playlist in playlists_result["items"]:
                playlists_full_res.append(playlist)

        for playlist in playlists_full_res:
            all_collections.append((playlist["name"], playlist["id"], playlist["tracks"]["href"]))
        
        # Convert each track collection to CSV file
        for col_name, col_id, col_url in all_collections:

            print "Backing up playlist: %s..." % col_name

            # Get all track results from API
            all_tracks = []
            try:
                tracks_result = sp._get(col_url)
            except spotify_web.SpotifyException:
                print "  The requested resource could not be found: %s" % col_url

            for track in tracks_result["items"]:
                all_tracks.append(track)
            while tracks_result["next"]:
                tracks_result = sp._get(tracks_result["next"])
                for track in tracks_result["items"]:
                    all_tracks.append(track)

            # Create CSV file 
            filename = "%s/%s - %s.csv" % (backup_dir, col_name, col_id)
            csvfile = open(filename, "w")
            writer = csv.writer(csvfile, 
                delimiter="\t",
                quoting=csv.QUOTE_MINIMAL,
            )

            # Header row
            writer.writerow([
                "artists",
                "album",
                "track",
                "album_disc",
                "album_index",
                "user",
                "added",
                "uri",
            ])

            for playlist_track in all_tracks:
                if playlist_track["track"]:
                    artist_names = ", ".join(art["name"] for art in playlist_track["track"]["artists"])

                    # Some playlists don't have the user data available.
                    if "added_by" in playlist_track and playlist_track["added_by"]:
                        user_id = playlist_track["added_by"]["id"]
                    else:
                        user_id = ""

                    row = [
                         artist_names,
                         playlist_track["track"]["album"]["name"],
                         playlist_track["track"]["name"],
                         playlist_track["track"]["disc_number"],
                         playlist_track["track"]["track_number"],
                         user_id,
                         playlist_track["added_at"],
                         playlist_track["track"]["uri"],
                    ]
        
                    cleanrow = []
                    for item in row:
                        if isinstance(item, basestring):
                            item = item.encode("utf-8")
                        cleanrow.append(item)
                    writer.writerow(cleanrow)

                else:
                    # I've seen one instance so far of a track in my library
                    # having an empty "track" object. 
                    print "Empty track object in playlist: %s" % col_name
                    writer.writerow([])

            print "  ...done."
                
        return None
