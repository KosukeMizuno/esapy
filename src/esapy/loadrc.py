#!/usr/bin/env python3

import os
from pathlib import Path
import yaml

from logging import getLogger
logger = getLogger(__name__)

KEY_TOKEN = 'ESA_PYTHON_TOKEN'
KEY_TEAM = 'ESA_PYTHON_TEAM'
RCFILE = '.esapyrc'

# esa > growi の優先順位で鍵を探す
KEY_GROWI_URL = 'GROWI_URL'
KEY_GROWI_USERNAME = 'GROWI_USERNAME'
KEY_GROWI_TOKEN = 'GROWI_TOKEN'


def _show_configuration():
    logger.info('showing configurations')
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

    print('environment variables for esa.io:')
    print('  %s=%s' % (KEY_TOKEN, os.environ.get(KEY_TOKEN, '')))
    print('  %s=%s' % (KEY_TEAM, os.environ.get(KEY_TEAM, '')))
    print('')
    print('environtme variables for growi:')
    print('  %s=%s' % (KEY_GROWI_TOKEN, os.environ.get(KEY_GROWI_TOKEN, '')))
    print('  %s=%s' % (KEY_GROWI_USERNAME, os.environ.get(KEY_GROWI_USERNAME, '')))
    print('  %s=%s' % (KEY_GROWI_URL, os.environ.get(KEY_GROWI_URL, '')))
    print('')


def get_token_and_team(args):
    """return tuple (token, team, dest)
    """
    x = None

    x = _get_token_from_args(args)
    if x is not None:
        logger.info('The token and teamname are set from args.')
        return x

    x = _get_token_from_environ()
    if x is not None:
        logger.info('The token and teamname are set from environ.')
        return x

    x = _get_token_from_rcfile()
    if x is not None:
        logger.info('The token and teamname are set from rcfile.')
        return x

    try:
        url = os.environ[KEY_GROWI_URL]
        _ = os.environ[KEY_GROWI_USERNAME]  # ここでは使用しないけど、エラーチェックのために読んでおく（クソハックなので直したいけどめんどい）
        if url[-1] == '/':
            url = url[:-1]  # 最後の / は除去
        x = (os.environ[KEY_GROWI_TOKEN], url, 'growi')
        return x
    except KeyError:
        raise KeyError('Environs for both of esa & growi are not found.')

    raise RuntimeError('Access token & team name were not found.  Please make $HOME/%s or set %s and %s.'
                       % (RCFILE, KEY_TOKEN, KEY_TEAM))


def _get_token_from_args(args):
    token, team = args.token, args.team

    if token is not None and team is not None:
        return token, team, 'esa'
    else:
        logger.debug('Getting token from args failed.')
        return None


def _get_token_from_environ():
    try:
        return os.environ[KEY_TOKEN], os.environ[KEY_TEAM], 'esa'
    except KeyError:
        logger.debug('Getting token from environ failed.')
        return None


def _get_rcfilepath():
    path_rc = Path.home() / RCFILE
    return path_rc


def _load_rcfile():
    path_rc = _get_rcfilepath()

    try:
        with path_rc.open('r', encoding='utf-8') as f:
            y = yaml.safe_load(f)

    except FileNotFoundError as e:
        y = {}

    return y


def _get_token_from_rcfile():
    x = None

    y = _load_rcfile()
    try:
        x = y['token'], y['team'], 'esa'
    except KeyError:
        logger.debug('Getting token from rcfile failed.')

    return x
