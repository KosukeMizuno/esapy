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


def upload_ipynb(filename, *, logger=None):
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


def upload_md(filename):
    pass


def upload_image(filename):
    pass


if __name__ == '__main__':
    main()

    upload_ipynb('/mnt/c/Users/MIZUNO/Documents/python/hatano_lab(GoogleDrive)/documents/instruments/S3-805 optics/gaussian beam.ipynb')
