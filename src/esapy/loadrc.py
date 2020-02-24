#!/usr/bin/env python3

import os
from pathlib import Path
import yaml


KEY_TOKEN = 'ESA_PYTHON_TOKEN'
KEY_TEAM = 'ESA_PYTHON_TEAM'
RCFILE = '.esapyrc'


def get_token_and_team():
    """return tuple (token, team)
    """
    x = None

    x = _load_token_from_environ()
    if x is not None:
        return x

    x = _load_token_from_rcfile()
    if x is not None:
        return x

    raise RuntimeError('Access token & team name were not found.  Please make $HOME/%s or set %s and %s.' % (RCFILE, KEY_TOKEN, KEY_TEAM))


def _load_token_from_environ():
    try:
        return os.environ[KEY_TOKEN], os.environ[KEY_TEAM]
    except KeyError:
        return None


def _load_rcfile():
    path_rc = Path.home() / RCFILE
    x = None

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
    print(_load_token_from_environ())
    print(_load_token_from_rcfile())

    print('')
    print(get_token_and_team())
