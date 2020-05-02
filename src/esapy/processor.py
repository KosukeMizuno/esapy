#!/usr/bin/env python3

from pathlib import Path
import shutil
import tempfile
import re
from urllib.parse import unquote

from .api import upload_binary, create_post
from .loadrc import get_token_and_team

# logger
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)


class EsapyProcessorBase(object):
    '''Base class

    ```python
    with Processor(path_workingdir) as proc:
        ...
    ```
    で呼ぶ
    '''

    FILETYPE_SUFFIX = '.md'

    def __init__(self, **kwargs):
        logger.info('Initializing processor={:s}'.format(self.__class__.__name__))
        self.args = dict(kwargs)

        self.path_input = Path(self.args['target']).resolve()  # target file
        logger.info('  input file={:s}'.format(str(self.path_input)))
        logger.info('  filetype={:s}'.format(self.path_input.suffix))

        self.path_root = Path(self.args['target']).parent  # root of relative pathes
        logger.info('  root of relative path={:s}'.format(str(self.path_root)))

        # check filetype
        if self.FILETYPE_SUFFIX != str(self.path_input.suffix):
            logger.warn('File type unmatched.')
            raise RuntimeError('File type unmatched.')

    def __enter__(self):
        logger.info('Securing temporal directory and files')

        # temporal working directory
        self.path_pwd = tempfile.mkdtemp(prefix=self.path_input.name, dir=self.path_input.parent)
        self.path_pwd = Path(self.path_pwd)
        logger.info('  temporal working directory={:s}'.format(str(self.path_pwd)))

        # intermediate markdown file ready to be uploaded
        _, self.path_md = tempfile.mkstemp(suffix='.md', dir=self.path_pwd)
        self.path_md = Path(self.path_md)
        logger.info('  intermediate markdown file={:s}'.format(str(self.path_md)))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info('Removing temporal working directory')
        shutil.rmtree(self.path_pwd)

    def preprocess(self):
        '''与えられたファイルを前処理する

        処理の中身：
        - 埋め込まれている画像があれば抽出する
        - 画像をアップロードする
        - 記事としてesaにアップするmarkdownファイルを作成する
        - 必要なら、他のファイルも一時ディレクトリ中に作成する

        Return:
          result of uploading images (bool)
        '''
        pass

    def upload_body(self):
        '''
        Return:
          result of uploading body (bool)
        '''
        pass

    def save(self):
        '''動作モードに応じて出力されたmdファイルを保存する
        '''
        pass


class MarkdownProcessor(EsapyProcessorBase):
    FILETYPE_SUFFIX = '.md'

    def preprocess(self):
        '''前から一行ずつ処理して画像をアップしていく
        処理後は一時mdファイルに保存する
        '''
        logger.info('Replacing & uploading images in target markdown file...')

        # replace & upload
        logger.info('Finding img tags ...')
        with self.path_input.open('r', encoding='utf-8') as f:
            md_body = f.readlines()
            md_body_modified = []

            for i, l in enumerate(md_body):
                _l = self._replace_line(i, l)
                md_body_modified.append(_l)

        logger.info('Replacing finished.')

        # save intermediate markdown
        self.path_md.open('w', encoding='utf-8').writelines(md_body_modified)
        logger.info('Intermediate markdown file has been saved.')

    def upload_body(self):
        pass

    def save(self):
        pass

    def _replace_line(self, i, l):
        '''一行分の処理

        画像タグを探して、あったらアップロード
        URLを取得して置き換えた一行を返す
        '''
        # find image tags
        matches = list(re.finditer(r'!\[(.*?)\]\((.+?)\)', l))
        if len(matches) > 1:
            logger.info('#{:d} line, {:d} image tags are found.'.format(i, len(matches)))
        elif len(matches) == 1:
            logger.info('#{:d} line, an image tag is found.'.format(i))
        else:
            # logger.debug('#{:d} line, no image is detected.'.format(i))
            return l

        logger.debug(l)

        # upload & replace
        _l = l
        for m in matches[::-1]:
            # path を抽出
            alttext, path_img = m.group(1), m.group(2)
            if len(path_img) > 4 and path_img[:4] == 'http':
                logger.info('  images referred via url -> pass, %s' % str(path_img))
                continue
            logger.info('  upload ... %s' % str(path_img))
            p = self.path_root / Path(unquote(path_img))

            # パス解決できるか確認
            pass

            # upload image
            try:
                url = upload_binary(p.resolve(),
                                    token=self.args['token'],
                                    team=self.args['team'],
                                    proxy=self.args['proxy'])

            except Exception as e:
                logger.warning(e)

            else:
                # upload succeeded.
                _l = _l[:m.start()] + '![%s](%s)' % (alttext, url) + _l[m.end():]

                pass #ここappendにしないとダメでは？

        return _l
