#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path
import tempfile
import mimetypes


import yaml
import requests


# logger
from logging import getLogger, StreamHandler, DEBUG
default_logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
default_logger.setLevel(DEBUG)
default_logger.addHandler(handler)
default_logger.propagate = False
default_logger.debug('esapy.upload loaded.')


def main():
    pass


def upload_ipynb(filename, outputname, *, logger=None):
    logger = logger or default_logger
    # ファイルパスの確認
    # 一時フォルダを確保
    # jupyter nbconvert で mdとpng生成
    # pngをアップロードし、アドレスを取得
    # md中の画像アドレスをアップロードしたものに置き換え
    # 数式環境$$ ~ $$ を mathコードブロックに置き換え
    # mdをアップロードする

    path_ipynb = Path(filename)
    logger.info('starting esapy#upload')
    logger.info('file: %s' % str(path_ipynb))

    #### file check ####
    if not path_ipynb.suffix == '.ipynb':
        raise RuntimeError('The assigned file (%s) is not a jupyter notebook.' % str(path_ipynb))

    ####
    with tempfile.TemporaryDirectory() as dname:
        path_tmpdir = Path(dname)
        logger.info('temporary directory: %s' % str(path_tmpdir))

        # process
        subprocess.check_call(['jupyter', 'nbconvert',
                               '--to=markdown',
                               '--output-dir=%s' % str(path_tmpdir),
                               '%s' % str(path_ipynb)
                               ])

        path_md = path_tmpdir / (path_ipynb.stem + '.md')
        path_list_img = list(path_tmpdir.glob('**/*.png'))
        logger.info('generated markdown: %s' % str(path_md))
        logger.info('generated images:')
        for p in path_list_img:
            logger.info('  %s' % str(path_md))

        # upload images
        pass

        # replace image url
        pass

        # replace math codeblock
        pass

        # upload markdown
        pass

    logger.info('ending esapy#upload')


def upload_md(filename, token, team, *, name=None, tags=None, category=None, wip=True, message=None, logger=None):
    """This function doesn't work.

    'URI too Large' ocurred.
    """
    logger = logger or default_logger

    path_md = Path(filename)
    logger.info('uploading markdown, %s' % str(path_md))

    md = path_md.open('r').read()

    # post
    url = 'https://api.esa.io/v1/teams/%s/posts' % team
    header = dict(Authorization='Bearer %s' % token)
    params = dict(name=name or "",
                  category=category or "",
                  message=message or "Upload post.",
                  body_md=md,
                  wip=wip)
    if isinstance(tags, list) and all([isinstance(t, str) for t in tags]):
        params['tags'] = tags

    res = requests.post(url, headers=header, params=params)

    print(res)
    pass

    return res


def upload_binary(filename, token, team, *, logger=None):
    logger = logger or default_logger

    path_bin = Path(filename)
    logger.info('uploading binary, %s' % str(path_bin))
    logger.info('  filesize: %d' % path_bin.stat().st_size)

    # get metadata
    url = 'https://api.esa.io/v1/teams/%s/attachments/policies' % team
    header = dict(Authorization='Bearer %s' % token)
    params = dict(type=mimetypes.guess_type(str(path_bin))[0],
                  name=path_bin.name,
                  size=path_bin.stat().st_size)
    res = requests.post(url, headers=header, params=params)

    if res.status_code != 200:
        logger.warning('Obtaining metadata failed, %s' % str(path_bin))
        raise RuntimeError('Obtaining metadata failed.')

    metadata = res.json()
    image_url = metadata['attachment']['url']

    logger.info('  metadata is obtained.')
    logger.debug(metadata)

    # upload file
    url = metadata['attachment']['endpoint']
    with path_bin.open('rb') as imgfile:
        params = metadata['form']
        params['file'] = imgfile
        res = requests.post(url, files=params)

    if not (200 <= res.status_code < 300):
        logger.warning('Upload failed, %s' % str(path_bin))
        raise RuntimeError('Upload failed.')
    logger.info('  the file is successfully uploaded, url: %s' % image_url)

    return image_url


if __name__ == '__main__':
    main()

