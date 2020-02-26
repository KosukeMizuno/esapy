#!/usr/bin/env python3

import os
from pathlib import Path
import yaml

from logging import getLogger


KEY_TOKEN = 'ESA_PYTHON_TOKEN'
KEY_TEAM = 'ESA_PYTHON_TEAM'
RCFILE = '.esapyrc'


def _show_configuration():
    path_rc = _get_rcfilepath()
    print('configuration file, "%s": ' % str(path_rc))
    try:
        with path_rc.open('r', encoding='utf-8') as f:
            ll = f.readlines()
            ll = ['  ' + l for l in ll]
            rc_body = ''.join(ll)
            print(rc_body)
    except FileNotFoundError as e:
        print('  rcFile not found.')

    if _load_token_from_environ() is not None:
        print('environment variables:')
        print('  %s=%s' % (KEY_TOKEN, os.environ.get(KEY_TOKEN, '')))
        print('  %s=%s' % (KEY_TEAM, os.environ.get(KEY_TEAM, '')))
        print('')


def get_token_and_team(args):
    """return tuple (token, team)
    """
    x = None

    x = _load_token_from_args(args)
    if x is not None:
        return x

    x = _load_token_from_environ()
    if x is not None:
        return x

    x = _load_token_from_rcfile()
    if x is not None:
        return x

    raise RuntimeError('Access token & team name were not found.  Please make $HOME/%s or set %s and %s.' % (RCFILE, KEY_TOKEN, KEY_TEAM))


def _load_token_from_args(args):
    try:
        token, team = args.token, args.team
    except AttributeError:
        return None

    if token is not None and team is not None:
        return token, team
    else:
        return None


def _load_token_from_environ():
    try:
        return os.environ[KEY_TOKEN], os.environ[KEY_TEAM]
    except KeyError:
        return None


def _get_rcfilepath():
    path_rc = Path.home() / RCFILE
    return path_rc


def _load_rcfile():
    path_rc = _get_rcfilepath()

    with path_rc.open('r') as f:
        y = yaml.safe_load(f)

    return y


def _load_token_from_rcfile():
    path_rc = Path.home() / RCFILE
    x = None

    with path_rc.open('r') as f:
        y = yaml.safe_load(f)
        try:
            x = y['token'], y['team']
        except:
            pass
    return x


if __name__ == '__main__':
    pass
