#!/usr/bin/env python3

from pathlib import Path
import json

# logger
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)


def reset_ipynb(target):
    logger.info('subcommand `Reset`')
    logger.info('  target={:s}'.format(target))
    path_target = Path(target)

    # type check
    if path_target.suffix != '.ipynb':
        logger.warning('target file is not jupyter notebook.')
        return
    
    # load
    with path_target.open('r', encoding='utf-8') as f:
        j = json.load(f)
    logger.info('Jupyter Notebook was loaded.')

    # reset metadata
    if 'esapy' not in j['metadata']:
        logger.info('No metadata regarding with esapy was detected.')
        return
    
    j['metadata'].pop('esapy', None)
    logger.info('Metadata was reset.')

    # save
    with path_target.open('w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        logger.info('Saved.')
