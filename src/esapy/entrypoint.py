#!/usr/bin/env python3

from pathlib import Path
import argparse
import webbrowser

from .loadrc import _show_configuration, get_token_and_team, RCFILE, KEY_TOKEN, KEY_TEAM
from .replace import _replace, _get_tempfile, _get_output_path, _remove_tempfile
from .convert import _call_converter
from .api import get_team_stats, create_post


# logger
from logging import getLogger, basicConfig, DEBUG, INFO
root_logger = getLogger(__package__)
logger = getLogger(__name__)


def command_up_old(args):
    # convert
    path_md = _call_converter(args)
    path_wd = path_md.parent

    # replace
    token, team = get_token_and_team(args)
    path_output = _get_output_path(path_md, args.output, args.no_output, args.destructive)

    body_md = _replace(path_input=path_md,
                       path_wd=path_wd,
                       path_output=path_output,
                       clipboard=args.clipboard,
                       token=token, team=team,
                       proxy=args.proxy)

    _remove_tempfile(path_output, args.output, args.no_output, args.destructive)

    # publish
    if args.publish:
        post_url = create_post(body_md,
                               name=args.name, tags=args.tag, category=args.category, wip=args.wip, message=args.message,
                               token=token, team=team, proxy=args.proxy)

        # TODO
        # if publish is failed, output temp file should be regenerated.

        if args.browser:
            edit_url = post_url + '/edit'
            logger.info('opening edit page ...')
            webbrowser.open(edit_url, new=2)


def command_up(args):
    print(args)


def command_stats(args):
    token, team = get_token_and_team(args)

    get_team_stats(token=token, team=team,
                   proxy=args.proxy)


def command_config(args):
    _show_configuration()


parser = argparse.ArgumentParser(description='Python implementation for esa.io.')
subparsers = parser.add_subparsers()

# up
parser_up = subparsers.add_parser('up', help='upload images & create/update post on esa.io',
                                  description='(1) Upload images referred from input file. (2) Create new post or update.')
parser_up.set_defaults(handler=command_up)
parser_up.add_argument('target', metavar='<input_filepath>', help='filename which you want to upload')

g_up_output = parser_up.add_argument_group(title='optional arguments for assigning output mode').add_mutually_exclusive_group()
g_up_output.add_argument('--destructive', action='store_true', default=True, help='[default] overwrite input file')
g_up_output.add_argument('--output', metavar='<output_filepath>', help='output filename')
g_up_output.add_argument('--no-output', action='store_true', help='work on temporary file')

g_up_mode = parser_up.add_argument_group('optional arguments for mode config')
g_up_mode.add_argument('--publish-mode', type=str, choices=['force', 'check', 'skip'], default='force', help='default is force. force: publish body even if uploading images failed, check: publish body when uploading succeeded, skip: create no post')
g_up_mode.add_argument('--post-mode', type=str, choices=['auto', 'new'], default='auto', help='default is auto. auto: when the file has been already uploaded, update the post (this function only for ipynb input), new: create new post always')
g_up_browse = g_up_mode.add_mutually_exclusive_group()
g_up_browse.add_argument('--open-browser', dest='browser', action='store_true', default=True, help='[default] open edit page on browser after publish')
g_up_browse.add_argument('--no-browser', dest='browser', action='store_false', help='skip opening edit page')

g_up_esa = parser_up.add_argument_group('optional arguments for esa.io post attributes')
g_up_esa.add_argument('--name', metavar='<post title>')
g_up_esa.add_argument('--category', metavar='<post category>')
g_up_esa.add_argument('--message', metavar='<post message>')
g_up_esa.add_argument('--tag', metavar='<post tag>', action='append', help='if your want to assign some tags, `--tag XXX --tag YYY`')
g_up_wip = g_up_esa.add_mutually_exclusive_group()
g_up_wip.add_argument('--wip', action='store_true', default=True, help='[default]')
g_up_wip.add_argument('--no-wip', dest='wip', action='store_false')

# stats
parser_stats = subparsers.add_parser('stats', help='show statistics of your team',
                                     description='Get statistics of your esa.io team. This command can be used as a connection test.')
parser_stats.set_defaults(handler=command_stats)

# config
parser_config = subparsers.add_parser('config', help='show your config',
                                      description="Show your config files and environment variables. Token and teamname can be addressed by rcfile ('~/%s'), environment variables ('%s', '%s'), and arguments ('--token', '--team'). The priority is args > environ > rcfile." % (RCFILE, KEY_TOKEN, KEY_TEAM))
parser_config.set_defaults(handler=command_config)

# common arguments
g_up_network = parser.add_argument_group('optional arguments for network config')
g_up_network.add_argument('--token', metavar='<esa.io_token>', help='your access token for esa.io (read/write required)')
g_up_network.add_argument('--team', metavar='<esa.io_team_name>', help='`***` of `https://***.esa.io/`')
g_up_network.add_argument('--proxy', metavar='<url>:<port>')
parser.add_argument('--verbose', '-v', action='count', default=0)


def main():
    # logger config
    basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s')

    # parse arguments
    args = parser.parse_args()

    # verbose level
    if args.verbose >= 2:
        root_logger.setLevel(DEBUG)
    elif args.verbose >= 1:
        root_logger.setLevel(INFO)
    logger.info('verbose level={:d}'.format(args.verbose))

    # call each function
    args.handler(args)


if __name__ == '__main__':
    main()
