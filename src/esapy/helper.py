#!/usr/bin/env python3

from pathlib import Path
import json

# logger
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)


def reset_ipynb(target, post_number=None, clear_hashdict=False):
    '''Remove metadata in <target> ipynb file,
    and write post_number in it if assigned.
    '''
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
        j['metadata']['esapy'] = dict()
        logger.info('Metadata was initialized.')

    # stash hashdict
    if clear_hashdict:
        h_dict = {}
        logger.info('Hash dict was cleared.')
    else:
        h_dict = j['metadata']['esapy'].get('hashdict', {})
        logger.info('Hash dict was stashed.')
    logger.debug(h_dict)

    # reset
    j['metadata']['esapy'] = dict(hashdict=h_dict)
    logger.info('Metadata was reset.')
    logger.debug(j['metadata'])

    # set post_number
    if post_number is not None:
        j['metadata']['esapy']['post_info'] = dict(number=post_number)
        logger.info('post_number={:d} has been set.'.format(post_number))

    # save
    with path_target.open('w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        logger.info('Saved.')


def ls_dir_or_file(filepath, use_fullpath=True, grid=True, recursive=True):
    """[summary]

    Parameters
    ----------
    filepath : str or Sequence[str]
    """
    if isinstance(filepath, str):
        lst_target = [filepath]
    else:
        lst_target = filepath

    lst = []  # (filename, is_uploaded, number)

    # make list
    def get_nb_info(path_nb):
        if path_nb.suffix != '.ipynb':
            return

        logger.info('an ipynb file is detected={:s}'.format(str(path_nb)))

        try:
            with path_nb.open('r', encoding='utf-8') as f:
                j = json.load(f)
        except FileNotFoundError:
            logger.info('  Opening {:s} failed.')
            return

        if 'esapy' not in j['metadata']:
            logger.info('  This file doesn\'t have esapy metadata.')
            lst.append((path_nb, False, None))
            return

        n = j['metadata']['esapy'].get('post_info', {}).get('number', None)
        if n is not None:
            logger.info('  Post number={:d}'.format(n))
            lst.append((path_nb, True, n))
        else:
            logger.info('  Unuploaded file.')
            lst.append((path_nb, False, None))

    # make list
    for fn_target in lst_target:
        path_target = Path(fn_target)
        if path_target.is_dir():
            logger.info('gathering ipynb list in {:s}'.format(str(path_target.resolve())))

            plist = path_target.glob('**/*.ipynb') if recursive else path_target.iterdir()
            for p in plist:
                get_nb_info(p)
        else:
            logger.info('gathering {:s}'.format(str(path_target.resolve())))
            get_nb_info(path_target)

    # length check
    if len(lst) == 0:
        print('No ipynb was found.')
        return

    lst = sorted(lst, key=lambda x: x[0])

    logger.info('showing file list')
    if grid:
        print(' post_number | filename ')
        print('-------------|------------')

    for path, is_uploaded, number in lst:
        n = '{:>12d}'.format(number) if number is not None else ' ' * 11 + '.'
        fn = str(path.absolute()) if use_fullpath else path.name
        g = '|' if grid else ''
        print('{:s} {:s} {:s}'.format(n, g, fn))


def get_version():
    import esapy

    try:
        import git
        r = git.Repo(Path(esapy.__file__).parents[2])
        return esapy.__version__ + '+' + str(r.head.commit)

    except Exception as e:
        return esapy.__version__
