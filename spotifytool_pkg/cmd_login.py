import os
import argparse
import subprocess

import command
import utils


class Login(command.Command):

    description="Store user login details, to be used by the Spotify web API"

    @classmethod
    def parse_args(self, args):
        parser = argparse.ArgumentParser(
            prog="spotifytool weblogin",
            description=self.description,
        )
        self._add_config_arg_to_parser(parser)

        return parser.parse_args(args)

    @classmethod
    def run(self, namespace):
        config = utils.read_config(namespace)
        oauth = utils.get_spotify_web_oauth(namespace)

        token_info = oauth.get_cached_token()
        if not token_info:
            auth_url = oauth.get_authorize_url()
            try:
                subprocess.call(["open", auth_url])
                print "Opening URL in your browser: \n%s" % auth_url
            except:
                print "Please navigate to login URL: \n%s" % auth_url
            response = raw_input("\nEnter the URL you were redirected to after login: ")
            code = oauth.parse_response_code(response)
            token_info = oauth.get_access_token(code)

        if token_info:
            print "Successfully authenticated for user: %s" % config["USER"]
        else:
            print "Failed to authenticate for user: %s" % config["USER"]

        return None
