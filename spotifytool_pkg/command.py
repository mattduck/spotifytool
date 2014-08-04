class Command(object):

    @classmethod
    def _add_config_arg_to_parser(self, parser):
        parser.add_argument("--config", "-c", 
            metavar="f",
            help="Path to spotifytool config file",
        )
        return None

    def parse_args(self):
        pass

    def run(self, namespace):
        pass
