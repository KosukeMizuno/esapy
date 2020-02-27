#!/usr/bin/env python3

import subprocess
from pathlib import Path

# logger
from logging import getLogger


def _call_converter(args, logger=None):
    logger = logger or getLogger(__name__)

    path_target = Path(args.target)
    ext = path_target.suffix
    path_output = path_target.with_suffix('.md')

    if ext == '.ipynb':
        logger.info('ipynb input ==> calling nbconvert, %s' % str(path_target))

        cmd = ['jupyter', 'nbconvert',
               '--to=markdown',
               '--output=%s' % str(path_output)]
        if args.verbose > 0:
            cmd.append('--debug')
        cmd.append(str(path_target))

        subprocess.check_call(cmd)

    elif ext == '.tex':
        logger.info('latex input ==> calling pandoc, %s' % str(path_target))

        cmd = ['pandoc',
               '-s', '%s' % str(path_target),
               '-o', '%s' % str(path_output)]

        subprocess.check_call(cmd)

    elif ext == '.md':
        logger.info('Input file is markdown. Nothing was done.')

    else:
        raise RuntimeError('unsupported file input, %s\nsupported format is .ipynb, .tex, or .md' % ext)

    return path_output
