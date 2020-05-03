#!/usr/bin/env python3

from pathlib import Path
import shutil
import tempfile
import re
from urllib.parse import unquote
import yaml
import subprocess

from .api import upload_binary, create_post, patch_post
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
        self.result_preprocess = self.result_upload = self.post_info = None

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
        if self.args['output'] is not None:
            # output が指定されている
            pass
        elif self.args['destructive']:
            # destructive mode
            pass
        else:
            # no-output mode
            pass

    def is_uploaded(self):
        '''アップロード履歴があるかどうか確認する

        あるなら、post_number を返す
        なければ None を返す
        '''
        pass

    def gather_post_info(self):
        '''gathering informatin for create/update post

        アップロード済みのmdなら、過去のyamlfrontmatterを基本にする
        引数による指定があればそちらを優先する
        tagに関しては上書きではなく追加していく

        Return: <dict>
          k/v ... 'name', 'tag', 'category','message': str
                  'wip': bool
        '''
        pass


class MarkdownProcessor(EsapyProcessorBase):
    FILETYPE_SUFFIX = '.md'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_yaml_frontmatter = None

    def __enter__(self):
        super().__enter__()

        # original markdown file excluded yaml frontmatter
        _, self.path_orig_body = tempfile.mkstemp(suffix='.md', dir=self.path_pwd)
        self.path_orig_body = Path(self.path_orig_body)
        logger.info('  original markdown file excluded YAML frontmatter={:s}'.format(str(self.path_orig_body)))

        return self

    def preprocess(self):
        '''前から一行ずつ処理して画像をアップしていく
        処理後は一時mdファイルに保存する
        YAML frontmatter があれば、除去しておく
        '''
        logger.info('Replacing & uploading images in target markdown file...')

        # replace & upload
        md_body_modified = []  # intermediate md
        res = []
        with self.path_input.open('r', encoding='utf-8') as f:
            md_body = f.readlines()

            # check yaml frontmatter
            if md_body[0].strip() == '---':  # yaml frontmatter exists
                for i, l in enumerate(md_body[1:]):  # find end of frontmatter, '---'
                    if l.strip() == '---':
                        ind_start_body = i + 1  # はじめの'---'を除いた分、一つずれてる
                        break
                yf = md_body[1:ind_start_body]  # frontmatter without '---'
                self.input_yaml_frontmatter = yaml.safe_load(''.join(yf))
                logger.info('YAML frontmatter is detected in input file.')
                logger.debug(self.input_yaml_frontmatter)
            else:
                ind_start_body = -1
                logger.debug('YAML frontmatter is not detected in input file.')

            # save original markdown without YAML
            self.path_orig_body.open('w', encoding='utf-8').writelines(md_body[ind_start_body + 1:])
            logger.info('Original markdown body excluded YAML frontmatter has been saved.')

            # process each line
            for i, l in enumerate(md_body[ind_start_body + 1:]):
                _l, _res = self._replace_line(i, l)
                md_body_modified.append(_l)
                res.extend(_res)

        logger.info('Replacing finished.')
        logger.debug(res)
        count_images = len([r for r in res if r[2] != 'http'])  # images which should be uploaded
        count_success = [r[2] for r in res].count('upload scceeded')  # images which are uploaded successfully
        logger.info('  {:d} image tags to be uploaded are detected.'.format(count_images))
        logger.info('  {:d} images are uploaded successfully.'.format(count_success))
        self.result_preprocess = (count_images == count_success)  # Are all uploadings succeeded ?

        # save intermediate markdown
        self.path_md.open('w', encoding='utf-8').writelines(md_body_modified)
        logger.info('Intermediate markdown file has been saved.')

        return self.result_preprocess

    def _replace_line(self, i, l):
        '''process single line
        '''
        res = []  # line, path,

        # find image tags
        matches = list(re.finditer(r'!\[(.*?)\]\((.+?)\)', l))
        if len(matches) > 1:
            logger.info('#{:d} line, {:d} image tags are found.'.format(i, len(matches)))
            logger.debug(l.strip())
        elif len(matches) == 1:
            logger.info('#{:d} line, an image tag is found.'.format(i))
            logger.debug(l.strip())
        else:
            # logger.debug('#{:d} line, no image is detected.'.format(i))
            return l, res

        # upload & replace
        _l = l
        res = []
        for m in matches[::-1]:  # 後ろから処理すると前にあるものはインデックスが変化しないので逆順に並べる
            # path を抽出
            alttext, fn_img = m.group(1), m.group(2)
            if len(fn_img) > 4 and fn_img[:4] == 'http':
                logger.info('  This image is referred via url={:s}'.format(fn_img))
                res.append((i, fn_img, 'http'))
                continue
            logger.info('  uploading, filepath={:s}'.format(fn_img))
            path_img = self.path_root / Path(unquote(fn_img))
            path_img = path_img.resolve()

            # パス解決できるか確認
            if not path_img.exists():
                logger.warn('  File not found, {:s}'.format(str(path_img)))
                res.append((i, str(path_img), 'file not found'))
                continue

            # upload image
            try:
                url, _ = upload_binary(path_img,
                                       token=self.args['token'],
                                       team=self.args['team'],
                                       proxy=self.args['proxy'])

            except Exception as e:
                logger.warning(e)
                res.append((i, str(path_img), 'upload failed'))

            else:  # upload succeeded.
                # replace file path with URL
                _l = _l[:m.start()] \
                    + '![%s](%s)' % (alttext, url) \
                    + _l[m.end():]
                res.append((i, str(path_img), 'upload scceeded'))

        return _l, res

    def upload_body(self):
        logger.info('Uploading markdown body ...')
        with self.path_md.open('r', encoding='utf-8') as f:
            md_body = f.readlines()
            md_body = ''.join(md_body)

        logger.info('Gathering information for create post')
        info_dict = self.gather_post_info()
        logger.debug(info_dict)

        post_number = self.get_post_number()
        if post_number is None:
            logger.info('This file has not been uploaded before. ==> create new post')
            post_url, res = create_post(md_body,
                                        name=info_dict['name'],
                                        tags=info_dict['tags'],
                                        category=info_dict['category'],
                                        wip=info_dict['wip'],
                                        message=info_dict['message'],
                                        token=self.args['token'],
                                        team=self.args['team'],
                                        proxy=self.args['proxy'])
        else:
            logger.info('This file has been already uploaded. ==> patch the post')
            post_url, res = patch_post(post_number, md_body,
                                       name=info_dict['name'],
                                       tags=info_dict['tags'],
                                       category=info_dict['category'],
                                       wip=info_dict['wip'],
                                       message=info_dict['message'],
                                       token=self.args['token'],
                                       team=self.args['team'],
                                       proxy=self.args['proxy'])

        self.post_info = res.json()
        self.result_upload = True

        return post_url

    def save(self):
        '''動作モードに応じて出力されたmdファイルを保存する
        '''
        with self.path_orig_body.open('r', encoding='utf-8') as f:
            md_body = f.readlines()
            md_body = ''.join(md_body)
        yf = self._get_yaml_frontmatter()
        logger.debug('YAML frontmatter:')
        logger.debug('{:s}'.format(yf))
        md_body = yf + md_body

        if self.args['output'] is not None:
            # output が指定されている
            p = Path(self.args['output'])
            logger.info('output file path={:s}'.format(str(p)))
            p.open('w', encoding='utf-8').writelines(md_body)

        elif self.args['destructive']:
            if self.result_upload:
                p = self.path_input
                logger.info('output file path is input file path={:s}'.format(str(p)))
                p.open('w', encoding='utf-8').writelines(md_body)
            else:
                logger.info('uploading body was failed, so saving is skipped.')

        else:
            logger.info('no-output mode')

    def _get_yaml_frontmatter(self):
        '''get yaml frontmatter for save derived from HTTP_RESPONSE
        '''
        if self.post_info is None:
            return ''

        yf = ['---',
              'title: "{:s}"'.format(self.post_info['name']),
              'category: {:s}'.format(self.post_info['category']),
              'tags: {:s}'.format(', '.join(self.post_info['tags'])),
              'created_at: {:s}'.format(self.post_info['created_at']),
              'updated_at: {:s}'.format(self.post_info['updated_at']),
              'published: {:s}'.format(str(not self.post_info['wip']).lower()),
              'number: {:s}'.format(str(self.post_info['number'])),
              '---\n']
        yf = '\n'.join(yf)
        return yf

    def gather_post_info(self):
        '''gathering informatin for create/update post

        アップロード済みのmdなら、過去のyamlfrontmatterを基本にする
        引数による指定があればそちらを優先する
        tagに関しては上書きではなく追加していく
        既にwip=falseの場合は、実行時引数を無視してwip=falseのままにする

        Return: <dict>
          k/v ... 'name', 'tag', 'category','message': str
                  'wip': bool
        '''
        yf = self.input_yaml_frontmatter if self.input_yaml_frontmatter is not None else {}
        d = {}

        # manage tags (None or list)
        d['tags'] = yf.get('tags', '').split(', ') if yf.get('tags', '') is not None else []
        if self.args['tags'] is not None:
            d['tags'].extend(self.args['tags'])
        d['tags'] = list(set(d['tags']))  # unique

        # wip (bool)
        d['wip'] = not (not self.args['wip'] or yf.get('published', False))

        # category, message (None or str)
        for k in ['category', 'message']:
            if self.args[k] is not None:
                d[k] = self.args[k]
            else:
                d[k] = yf.get(k, None)

        # name in args > title in yaml-frontmatter
        if self.args['name'] is not None:
            d['name'] = self.args['name']
        else:
            d['name'] = yf.get('title', None)

        return d

    def get_post_number(self):
        '''YAML formatter をみて、アップロード履歴があるかどうか確認する
        アップロード済み: post_number
        アップロード初めて: None
        '''
        if self.input_yaml_frontmatter is None:
            return None
        elif 'number' not in self.input_yaml_frontmatter:
            return None

        return self.input_yaml_frontmatter['number']

    def is_uploaded(self):
        n = self.get_post_number()
        return n is not None


class TexProcessor(MarkdownProcessor):
    '''pandoc を読んで、その出力をpath_inputにしてからMarkdownProcessor（親クラス）にわたす
    '''

    FILETYPE_SUFFIX = '.tex'

    def is_uploaded(self):
        return False

    def preprocess(self):
        logger.info('Calling pandoc')
        cmd = ['pandoc',
               '-s', '{:s}'.format(str(self.path_input)),
               '-o', '{:s}'.format(str(self.path_md))]
        logger.debug(cmd)

        res = subprocess.check_call(cmd)
        logger.debug(res)

        self.path_input = self.path_md

        # call preprocess of MarkdownProcessor
        super().preprocess()

    def gather_post_info(self):
        return self.args

    def save(self):
        '''動作モードに応じて出力されたmdファイルを保存する
        '''
        if self.args['output'] is not None:
            with self.path_orig_body.open('r', encoding='utf-8') as f:
                md_body = f.readlines()
                md_body = ''.join(md_body)
            yf = self._get_yaml_frontmatter()
            logger.debug('YAML frontmatter:')
            logger.debug('{:s}'.format(yf))
            md_body = yf + md_body

            # output が指定されている
            p = Path(self.args['output'])
            logger.info('output file path={:s}'.format(str(p)))
            p.open('w', encoding='utf-8').writelines(md_body)

        elif self.args['destructive']:
            logger.info('Nothing was done at #save in destructive mode of TexProcessor.')

        else:
            logger.info('no-output mode')


class IpynbProcessor_via_nbconvert(MarkdownProcessor):
    '''nbconvert を呼んで、その出力をpath_inputにしてからMarkdownProcessor（親クラス）にわたす
    '''

    FILETYPE_SUFFIX = '.ipynb'

    def is_uploaded(self):
        return False

    def preprocess(self):
        logger.info('Calling pandoc')
        cmd = ['jupyter', 'nbconvert',
               '--to=markdown',
               '--output={:s}'.format(str(self.path_md)),
               '--output-dir={:s}'.format(str(self.path_pwd)),
               '--log-level={:d}'.format(logger.level),
               '{:s}'.format(str(self.path_input))]
        logger.debug(cmd)

        res = subprocess.check_call(cmd)
        logger.debug(res)

        self.path_input = self.path_md

        # call preprocess of MarkdownProcessor
        super().preprocess()

    def gather_post_info(self):
        return self.args

    def save(self):
        '''動作モードに応じて出力されたmdファイルを保存する
        '''
        if self.args['output'] is not None:
            with self.path_orig_body.open('r', encoding='utf-8') as f:
                md_body = f.readlines()
                md_body = ''.join(md_body)
            yf = self._get_yaml_frontmatter()
            logger.debug('YAML frontmatter:')
            logger.debug('{:s}'.format(yf))
            md_body = yf + md_body

            # output が指定されている
            p = Path(self.args['output'])
            logger.info('output file path={:s}'.format(str(p)))
            p.open('w', encoding='utf-8').writelines(md_body)

        elif self.args['destructive']:
            logger.info('Nothing was done at #save in destructive mode of IpynbProcessor_via_nbconvert.')

        else:
            logger.info('no-output mode')
