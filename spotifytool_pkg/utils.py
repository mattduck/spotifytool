import os
import sys
import ConfigParser
import threading

import spotify as spotify_lib
import spotipy as spotify_web
from spotipy import oauth2 as spotify_web_oauth


def get_spotify_web_oauth(namespace):
    config = read_config(namespace)

    scope = " ".join([
        "playlist-modify-public",
        "playlist-modify-private",
        "playlist-read-private",
        "user-library-modify",
        "user-library-read",
        "user-read-private",
        "user-read-email",
        "streaming",
    ])

    cache_dir = os.path.join(config["CACHE_PATH"], "web_api")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Different cache file for each user
    full_cache_path = os.path.join(cache_dir, config["USER"])

    oauth = spotify_web_oauth.SpotifyOAuth(
        client_id=config["WEB_API_CLIENT_ID"],
        client_secret=config["WEB_API_CLIENT_SECRET"],
        redirect_uri=config["WEB_API_REDIRECT_URL"],
        cache_path=full_cache_path,
        scope=scope,
        state=None,
    )

    return oauth


def get_spotify_lib_session(namespace):
    config = read_config(namespace)

    # Wait for the session to login before returning, as recommended in
    # pyspotify docs. 

    logged_in_event = threading.Event()

    def _connection_state_listener(session):
        if session.connection.state is spotify_lib.ConnectionState.LOGGED_IN:
            logged_in_event.set()

    cache_dir = os.path.join(config["CACHE_PATH"], "libspotify")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    full_cache_path = os.path.join(cache_dir, config["USER"])

    spotify_config = spotify_lib.Config()
    spotify_config.cache_location = full_cache_path
    spotify_config.settings_location = full_cache_path
    spotify_config.load_application_key_file(config["LIBSPOTIFY_KEYFILE"])

    session = spotify_lib.Session(config=spotify_config)

    loop = spotify_lib.EventLoop(session)
    loop.start()

    session.on(
        spotify_lib.SessionEvent.CONNECTION_STATE_UPDATED,
        _connection_state_listener
    )

    session.login(config["USER"], config["PW"])
    logged_in_event.wait()

    return session
    

def read_config(namespace):
    """ Read given or default config file """

    given_config = namespace.config

    if given_config:
        given_config = os.path.expanduser(given_config)
        if not os.path.exists(given_config):
            print "--config path does not exist, exiting: %" % given_config
            sys.exit()
        config_path = given_config
    else:
        default_config_path = os.path.expanduser("~/.spotifytoolconfig")
        if not os.path.isfile(default_config_path):
            print "--config file not given and file not found at %s, exiting." % default_config_path
            sys.exit()
        config_path = default_config_path

    config_path = os.path.abspath(config_path)
    config = ConfigParser.ConfigParser()
    config.read(config_path)

    values = {}
    values["WEB_API_CLIENT_ID"] = config.get("spotify", "web_api_client_id")
    values["WEB_API_CLIENT_SECRET"] = config.get("spotify", "web_api_client_secret")
    values["USER"] = config.get("spotify", "user")
    values["PW"] = config.get("spotify", "password")
    values["COUNTRY"] = config.get("spotify", "country")

    redirect = config.get("spotify", "web_api_redirect_url")
    if not redirect.startswith("http"):
        print "Config value 'web_api_redirect_url' must begin with 'http'. Bad "\
        "value: %s" % redirect
        sys.exit()
    values["WEB_API_REDIRECT_URL"] = redirect

    # If the libspotify key file location is given as a relative path, join it
    # to the absoulte dir of the config file.
    keyfile = os.path.expanduser(config.get("spotify", "libspotify_keyfile"))
    if not os.path.isabs(keyfile):
        config_dir = os.path.split(config_path)[0]
        keyfile = os.path.abspath(os.path.join(config_dir, keyfile))
    values["LIBSPOTIFY_KEYFILE"] = keyfile

    # Same for cache path
    cache_path = os.path.expanduser(config.get("spotify", "cache_path"))
    if not os.path.isabs(cache_path):
        config_dir = os.path.split(config_path)[0]
        cache_path = os.path.abspath(os.path.join(config_dir, cache_path))
    values["CACHE_PATH"] = cache_path

    return values
