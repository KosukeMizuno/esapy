#!/usr/bin/env python3

from pathlib import Path
import argparse
import webbrowser
import sys

from .processor import MarkdownProcessor, TexProcessor, IpynbProcessor
from .loadrc import _show_configuration, get_token_and_team, RCFILE, KEY_TOKEN, KEY_TEAM
from .api import get_team_stats
from .helper import reset_ipynb, ls_dir_or_file, get_version

# logger
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)


def command_up(args):
    logger.info("starting 'esa up' ...")

    # check file-type
    suffix = Path(args.target).suffix
    proc_dict = {'.ipynb': IpynbProcessor,
                 '.md': MarkdownProcessor,
                 '.tex': TexProcessor}
    if suffix not in proc_dict.keys():
        logger.warning('Unsupported input file type')
        return
    proc_class = proc_dict[suffix]
    logger.info('Processoer={:s} is selected.'.format(proc_class.__name__))

    # set token & team
    args_dict = dict(vars(args))
    token, team = get_token_and_team(args)
    args_dict['token'] = token
    args_dict['team'] = team

    # process start
    browser_flg = False  # flag to open browser after uploading body
    with proc_class(**args_dict) as proc:
        # upload images
        res_preprocess = proc.preprocess()

        # mode check
        if args.publish_mode == 'force':
            publish_flg = True
        elif args.publish_mode == 'check':
            publish_flg = res_preprocess
        else:  # 'skip'
            publish_flg = False
        logger.info('publish mode={:s}, result of preprocess={:s}, ... publish: {:s}'
                    .format(args.publish_mode, str(res_preprocess), str(publish_flg)))

        # publish body
        if publish_flg:
            try:
                post_url = proc.upload_body()
                browser_flg = args.browser
                logger.info('post_url={:s}'.format(post_url))
                print('post page URL ... {:s}'.format(post_url))
            except RuntimeError as e:
                tb = sys.exc_info()[2]
                logger.warn(e)
                logger.warn(e.with_traceback(tb))

        # finalize
        proc.save()

    # if succeeded, open browser in edit page
    if browser_flg:
        edit_url = post_url + '/edit'
        logger.info('edit page={:s}'.format(edit_url))
        print('edit page URL ... {:s}'.format(edit_url))
        webbrowser.open(edit_url, new=2)


def command_stats(args):
    token, team = get_token_and_team(args)

    try:
        st = get_team_stats(token=token, team=team,
                            proxy=args.proxy)
        print(st)
    except RuntimeError as e:
        print('Failed: please check network settings (token, team, proxy)')


def command_config(args):
    _show_configuration()


def command_reset(args):
    reset_ipynb(args.target, args.number, args.clear_hashdict)


def command_ls(args):
    ls_dir_or_file(args.target,
                   use_fullpath=(args.mode == 'full'),
                   grid=not args.no_grid,
                   recursive=args.recursive)


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
parser_up.add_argument('--leave-temp', action='store_true', help='leave temporary files')

g_up_mode = parser_up.add_argument_group('optional arguments for mode config')
g_up_mode.add_argument('--folding-mode', type=str, choices=['auto', 'as-shown', 'ignore'], default='auto', help='default is auto. ignore: any details tag will be set as open, as-shown: details tags obey metadata of each cell, auto: source block of code-cell starting from "plt.figure" will be closed.')
g_up_mode.add_argument('--publish-mode', type=str, choices=['force', 'check', 'skip'], default='force', help='default is force. force: publish body even if uploading images failed, check: publish body when uploading succeeded, skip: create no post')
g_up_mode.add_argument('--post-mode', type=str, choices=['auto', 'new'], default='auto', help='default is auto. auto: when the file has been already uploaded, update the post (this function only for ipynb input), new: create new post always')
g_up_browse = g_up_mode.add_mutually_exclusive_group()
g_up_browse.add_argument('--open-browser', dest='browser', action='store_true', default=True, help='[default] open edit page on browser after publish')
g_up_browse.add_argument('--no-browser', dest='browser', action='store_false', help='skip opening edit page')

g_up_esa = parser_up.add_argument_group('optional arguments for esa.io post attributes')
g_up_esa.add_argument('--name', metavar='<post title>')
g_up_esa.add_argument('--category', metavar='<post category>')
g_up_esa.add_argument('--message', metavar='<post message>')
g_up_esa.add_argument('--tag', dest='tags', metavar='<post tag>', action='append', help='if your want to assign some tags, `--tag XXX --tag YYY`')
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

# reset
parser_reset = subparsers.add_parser('reset', help='reset metadata',
                                     description='Clear post_number of esapy in ipynb metadata, or set post_number if given')
parser_reset.set_defaults(handler=command_reset)
parser_reset.add_argument('target', metavar='<filepath>.ipynb', help='notebook file which you want to reset')
parser_reset.add_argument('--number', metavar='<post_number>', type=int, help='post_number to newly set')
parser_reset.add_argument('--clear-hashdict', action='store_true', help='clear hashdict (map of uploaded images and urls)')

# ls
parser_ls = subparsers.add_parser('ls', help='show ipynb file list',
                                  description='Show list of ipynb files and its post number if it has been uploaded.')
parser_ls.set_defaults(handler=command_ls)
parser_ls.add_argument('target', metavar='<target>', default='.', nargs='*', help='filepath of ipynb or directory')
parser_ls.add_argument('--mode', type=str, choices=['full', 'base'], default='full', help='filename as full-path or basename, default is full.')
parser_ls.add_argument('--no-grid', action='store_true', help='print only post_number and filename')
parser_ls.add_argument('--recursive', action='store_true', help='scan subfolder recursively')

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
    if args.verbose >= 3:
        getLogger().setLevel(0)  # root logger
    elif args.verbose >= 2:
        getLogger(__package__).setLevel(DEBUG)  # package logger
    elif args.verbose >= 1:
        getLogger(__package__).setLevel(INFO)  # package logger
    logger.info('esapy version={:s}'.format(get_version()))
    logger.info('verbose level={:d}'.format(args.verbose))
    logger.debug('args={:s}'.format(str(args)))

    # call each function
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
