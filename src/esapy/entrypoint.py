#!/usr/bin/env python3

from pathlib import Path
import argparse

from .loadrc import _show_configuration, get_token_and_team
from .replace import _replace
from .convert import _call_converter


# logger
from logging import getLogger, StreamHandler, FileHandler, DEBUG
logger = getLogger(__name__)
logger.addHandler(StreamHandler())


def command_up(args):
    # convert
    path_md = _call_converter(args, logger=logger)

    # replace
    token, team = get_token_and_team(args)

    _replace(path_input=Path(args.target_md),
             clipboard=args.clipboard,
             token=token, team=team,
             proxy=args.proxy,
             logger=logger)


def command_convert(args):
    _call_converter(args, logger=logger)


def command_replace(args):
    token, team = get_token_and_team(args)

    _replace(path_input=Path(args.target_md),
             clipboard=args.clipboard,
             token=token, team=team,
             proxy=args.proxy,
             logger=logger)


def command_publish(args):
    pass


def command_config(args):
    _show_configuration()


parser = argparse.ArgumentParser(description='Python implementation for esa.io.')
subparsers = parser.add_subparsers()

# up
parser_up = subparsers.add_parser('up', help='convert & upload images & generate modified markdown')
parser_up.set_defaults(handler=command_up)
parser_up.add_argument('target', metavar='<input_filepath>', help='filename which you want to upload')
parser_up.add_argument('--clipboard', '-c', action='store_true', default=None, help='go markdown body to clipborad after process')
parser_up.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
parser_up.add_argument('--team', metavar='<esa.io_team_name>', help='*** of `https://***.esa.io/`')
parser_up.add_argument('--proxy', metavar='<url>:<port>')
parser_up.add_argument('--verbose', '-v', action='count', default=0)

# convert
parser_conv = subparsers.add_parser('convert', help='[subcommand] convert file as to markdown')
parser_conv.set_defaults(handler=command_convert)
parser_conv.add_argument('target', metavar='<input_filepath>', help='filename which you want to upload')
parser_conv.add_argument('--verbose', '-v', action='count', default=0)

# replace & upload
parser_replace = subparsers.add_parser('replace', help='[subcommand] find img references in markdown, upload image if its path is relative, and replace path to url')
parser_replace.set_defaults(handler=command_replace)
parser_replace.add_argument('target_md', metavar='<input_filepath (markdown file)>')
parser_replace.add_argument('--clipboard', '-c', action='store_true', default=None, help='go markdown body to clipborad after process')
parser_replace.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
parser_replace.add_argument('--team', metavar='<esa.io_team_name>', help='*** of `https://***.esa.io/`')
parser_replace.add_argument('--proxy', metavar='<url>:<port>')
parser_replace.add_argument('--verbose', '-v', action='count', default=0)

# publish <target.md>
pass

# config
parser_config = subparsers.add_parser('config', help='show your config files')
parser_config.set_defaults(handler=command_config)


def main():
    args = parser.parse_args()

    try:
        if args.verbose > 0:
            logger.setLevel(DEBUG)
            print("@@@@")
    except AttributeError:
        pass

    args.handler(args)


if __name__ == '__main__':
    main()
