#!/usr/bin/env python3

from pathlib import Path
import argparse

from .loadrc import _show_configuration, get_token_and_team
from .replace import _replace
from .convert import _call_converter
from .api import get_team_stats, create_post


# logger
from logging import getLogger, StreamHandler, FileHandler, DEBUG, INFO
logger = getLogger(__name__)
logger.addHandler(StreamHandler())


def command_up(args):
    # convert
    path_md = _call_converter(args, logger=logger)
    path_wd = path_md.parent

    # replace
    token, team = get_token_and_team(args)

    body_md = _replace(path_input=path_md,
                       path_wd=path_wd,
                       clipboard=args.clipboard,
                       token=token, team=team,
                       proxy=args.proxy,
                       logger=logger)

    # publish
    if args.publish:
        create_post(body_md,
                    name=args.name, tags=args.tag, category=args.category, wip=args.wip, message=args.message,
                    token=token, team=team, proxy=args.proxy,
                    logger=logger)


def command_convert(args):
    _call_converter(args, logger=logger)


def command_replace(args):
    token, team = get_token_and_team(args)

    _replace(path_input=Path(args.target_md),
             path_wd=Path(args.target_md).parent,
             clipboard=args.clipboard,
             token=token, team=team,
             proxy=args.proxy,
             logger=logger)


def command_stats(args):
    token, team = get_token_and_team(args)

    get_team_stats(token=token, team=team,
                   proxy=args.proxy,
                   logger=logger)


def command_publish(args):
    path_md = Path(args.target_md)
    body_lines = path_md.open('r', encoding='utf-8').readlines()
    body_md = ''.join(body_lines)

    token, team = get_token_and_team(args)

    create_post(body_md,
                name=args.name, tags=args.tag, category=args.category, wip=args.wip, message=args.message,
                token=token, team=team, proxy=args.proxy,
                logger=logger)


def command_config(args):
    _show_configuration()


parser = argparse.ArgumentParser(description='Python implementation for esa.io.')
subparsers = parser.add_subparsers()

# up
parser_up = subparsers.add_parser('up', help='convert & upload images & generate modified markdown')
parser_up.set_defaults(handler=command_up)
parser_up.add_argument('target', metavar='<input_filepath>', help='filename which you want to upload')
g_up_clip = parser_up.add_mutually_exclusive_group()
g_up_clip.add_argument('--clipboard', action='store_true', default=None, help='go markdown body to clipborad after process')
g_up_clip.add_argument('--no-clipboard', action='store_false', dest='clipboard')

g_up_publish = parser_up.add_mutually_exclusive_group()
g_up_publish.add_argument('--publish', action='store_true', default=True, help='publish markdown')
g_up_publish.add_argument('--no-publish', action='store_false', dest='publish')
parser_up.add_argument('--name', metavar='<post title>')
parser_up.add_argument('--category', metavar='<post category>')
parser_up.add_argument('--message', metavar='<post message>')
parser_up.add_argument('--tag', metavar='<post tag>', action='append', help='if your want to assign some tags, `--tag XXX --tag YYY`')
g_up_wip = parser_up.add_mutually_exclusive_group()
g_up_wip.add_argument('--wip', action='store_true', default=True)
g_up_wip.add_argument('--no-wip', dest='wip', action='store_false')

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
g_rep_clip = parser_replace.add_mutually_exclusive_group()
g_rep_clip.add_argument('--clipboard', action='store_true', default=None, help='go markdown body to clipborad after process')
g_rep_clip.add_argument('--no-clipboard', action='store_false', dest='clipboard')
parser_replace.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
parser_replace.add_argument('--team', metavar='<esa.io_team_name>', help='*** of `https://***.esa.io/`')
parser_replace.add_argument('--proxy', metavar='<url>:<port>')
parser_replace.add_argument('--verbose', '-v', action='count', default=0)

# publish <target.md>
parser_publish = subparsers.add_parser('publish', help='show statistics of your team')
parser_publish.set_defaults(handler=command_publish)
parser_publish.add_argument('target_md', metavar='<input_filepath (markdown file)>')
parser_publish.add_argument('--name', metavar='<post title>')
parser_publish.add_argument('--category', metavar='<post category>')
parser_publish.add_argument('--message', metavar='<post message>')
parser_publish.add_argument('--tag', metavar='<post tag>', action='append', help='if your want to assign some tags, `--tag XXX --tag YYY`')
g_pub_wip = parser_publish.add_mutually_exclusive_group()
g_pub_wip.add_argument('--wip', action='store_true', default=True)
g_pub_wip.add_argument('--no-wip', dest='wip', action='store_false')
parser_publish.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
parser_publish.add_argument('--team', metavar='<esa.io_team_name>', help='*** of `https://***.esa.io/`')
parser_publish.add_argument('--proxy', metavar='<url>:<port>')
parser_publish.add_argument('--verbose', '-v', action='count', default=0)

# replace & upload
parser_stats = subparsers.add_parser('stats', help='show statistics of your team')
parser_stats.set_defaults(handler=command_stats)
parser_stats.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
parser_stats.add_argument('--team', metavar='<esa.io_team_name>', help='*** of `https://***.esa.io/`')
parser_stats.add_argument('--proxy', metavar='<url>:<port>')
parser_stats.add_argument('--verbose', '-v', action='count', default=0)

# config
parser_config = subparsers.add_parser('config', help='show your config files')
parser_config.set_defaults(handler=command_config)


def main():
    args = parser.parse_args()

    try:
        if args.verbose > 1:
            logger.setLevel(DEBUG)
        elif args.verbose > 0:
            logger.setLevel(INFO)
    except AttributeError:
        pass

    args.handler(args)


if __name__ == '__main__':
    main()
