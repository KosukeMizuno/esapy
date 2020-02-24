#!/usr/bin/env python3

import pyperclip
from .loadrc import _load_rcfile


def go_clipboard(md_body, logger):
    cfg = _load_rcfile()
    flg = cfg.get('tool', {}).get('goto_clipboard', False)

    if flg:
        pyperclip.copy(md_body)
        logger.info('Markdown body is copied to clipboard.')
