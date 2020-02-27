#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote
import pyperclip

from .api import upload_binary
from .loadrc import _load_rcfile

# logger
from logging import getLogger


def _replace(path_input, clipboard=False, token=None, team=None, proxy=None, logger=None):
    logger = logger or getLogger(__name__)
    logger.info('Replace & upload images in %s' % str(path_input))

    # replace & upload
    logger.info('Finding img tags ...')
    with path_input.open('r', encoding='utf-8') as f:
        md_body = f.readlines()
        md_body_modified = []

        for i, l in enumerate(md_body):
            _l = _replace_line(i, l, token, team, proxy, logger=logger)
            md_body_modified.append(_l)

    logger.info('Replace finished.')

    # goto clipboard
    _go_clipboard(''.join(md_body_modified), clipboard, logger)

    # save modified markdonwn
    path_output = path_input
    path_output.open('w', encoding='utf-8').writelines(md_body_modified)
    logger.info('Modified markdown is saved as %s' % str(path_output))

    return ''.join(md_body_modified)

def _replace_line(i, l, token, team, proxy, logger=None):
    logger = logger or getLogger(__name__)

    # find image tags
    matches = list(re.finditer(r'!\[(.+?)\]\((.+?)\)', l))
    if len(matches) > 1:
        logger.info('#%d line, %d image tags are found.' % (i, len(matches)))
    elif len(matches) == 1:
        logger.info('#%d line, an image tag is found.' % i)
    else:
        return l

    # upload & replace
    _l = l
    for m in matches[::-1]:
        alttext, path_img = m.group(1), m.group(2)
        if len(path_img) > 4 and path_img[:4] == 'http':
            logger.info('  images referred via url -> pass, %s' % str(path_img))
            continue

        logger.info('  upload ... %s' % str(path_img))
        p = Path(unquote(path_img))
        try:
            url = upload_binary(p, token=token, team=team, proxy=proxy, logger=logger)

        except Exception as e:
            logger.warning(e)

        else:
            # upload succeeded.
            _l = _l[:m.start()] + '![%s](%s)' % (alttext, url) + _l[m.end():]

    return _l


def _go_clipboard(md_body, args_flg, logger=None):
    """flg in args > flg in rc file
    """
    logger = logger or getLogger(__name__)

    cfg = _load_rcfile()
    rc_flg = cfg.get('tool', {}).get('goto_clipboard', False)

    if args_flg is None:
        flg = rc_flg
    else:
        flg = args_flg

    if flg:
        pyperclip.copy(md_body)
        logger.info('Markdown body is copied to clipboard.')
