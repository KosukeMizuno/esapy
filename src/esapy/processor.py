#!/usr/bin/env python3

from pathlib import Path
import shutil
import tempfile
import re
import os
from urllib.parse import unquote
import yaml
import subprocess
import base64
import hashlib
import json

from .api import upload_binary, create_post, patch_post, get_post
from .loadrc import get_token_and_team
from .helper import get_version

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

        # os file descriptor
        self._fd_list = []

        # temporal working directory
        self.path_pwd = tempfile.mkdtemp(prefix=self.path_input.name, dir=self.path_root)
        self.path_pwd = Path(self.path_pwd)
        logger.info('  temporal working directory={:s}'.format(str(self.path_pwd)))

        # intermediate markdown file ready to be uploaded
        fd, self.path_md = tempfile.mkstemp(suffix='.md', dir=self.path_pwd)
        self._fd_list.append(fd)
        self.path_md = Path(self.path_md)
        logger.info('  intermediate markdown file={:s}'.format(str(self.path_md)))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for fd in self._fd_list:
            os.close(fd)

        if not self.args['leave_temp']:
            logger.info('Removing temporal working directory')
            shutil.rmtree(self.path_pwd)
        else:
            logger.info('Leave temporary files.')

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
        return False

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
        fd, self.path_orig_body = tempfile.mkstemp(suffix='.md', dir=self.path_pwd)
        self._fd_list.append(fd)
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
            with self.path_orig_body.open('w', encoding='utf-8') as f:
                f.writelines(md_body[ind_start_body + 1:])
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
        with self.path_md.open('w', encoding='utf-8') as f:
            f.writelines(md_body_modified)
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
        if post_number is None or self.args['post_mode'] == 'new':
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
            with p.open('w', encoding='utf-8') as f:
                f.writelines(md_body)

        elif self.args['destructive']:
            if self.result_upload:
                p = self.path_input
                logger.info('output file path is input file path={:s}'.format(str(p)))
                with p.open('w', encoding='utf-8') as f:
                    f.writelines(md_body)
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
            with p.open('w', encoding='utf-8') as f:
                f.writelines(md_body)

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
            with p.open('w', encoding='utf-8') as f:
                f.writelines(md_body)

        elif self.args['destructive']:
            logger.info('Nothing was done at #save in destructive mode of IpynbProcessor_via_nbconvert.')

        else:
            logger.info('no-output mode')


class IpynbProcessor(EsapyProcessorBase):
    FILETYPE_SUFFIX = '.ipynb'
    SCROLL_HEIGHT = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nbjson = None

    def __enter__(self):
        super().__enter__()

        # intermediate ipynb file
        fd, self.path_ipynb = tempfile.mkstemp(suffix='.ipynb', dir=self.path_pwd)
        self._fd_list.append(fd)
        self.path_ipynb = Path(self.path_ipynb)
        logger.info('  intermediate ipynb file={:s}'.format(str(self.path_ipynb)))

        return self

    def preprocess(self):
        # load ipynb
        with self.path_input.open('r', encoding='utf-8') as f:
            self.nbjson = json.load(f)
        logger.info('Jupyter Notebook ({:s}) was loaded.'.format(str(self.path_input)))

        # check nbformat version
        logger.debug('  nbformat={:d}.{:d}'.format(self.nbjson['nbformat'], self.nbjson['nbformat_minor']))
        if self.nbjson['nbformat'] != 4:
            logger.warn('This program supports nbformat=4.x')

        # info of notebook
        self.language = self.nbjson['metadata']['kernelspec']['language']

        # initialize metadata if required.
        if 'esapy' not in self.nbjson['metadata']:
            self.nbjson['metadata']['esapy'] = {}
            logger.debug('Notebook metadata initialized.')
        if 'post_info' not in self.nbjson['metadata']['esapy']:
            self.nbjson['metadata']['esapy']['post_info'] = {}
            logger.debug('Notebook previous post_info initialized.')
        if 'number' not in self.nbjson['metadata']['esapy']['post_info']:
            self.nbjson['metadata']['esapy']['post_info']['number'] = None
            logger.info('This notebook has not been uploaded at esa.io.')
        if 'hashdict' not in self.nbjson['metadata']['esapy']:
            self.nbjson['metadata']['esapy']['hashdict'] = {}  # key=sha256, value=url
            logger.debug('Notebook hash_dict initialized.')

        # Process each cell
        logger.info('Processing {:d} cells...'.format(len(self.nbjson['cells'])))
        md_body = []
        for cell in self.nbjson['cells']:
            proc_func = {'raw': self._process_cell_raw,
                         'markdown': self._process_cell_md,
                         'code': self._process_cell_code}[cell['cell_type']]
            md_body.extend(proc_func(cell))

        # save temprorary files
        with self.path_md.open('w', encoding='utf-8') as f:
            f.writelines(md_body)
        logger.info('Intermediate md file has been saved.')
        with self.path_ipynb.open('w', encoding='utf-8') as f:
            json.dump(self.nbjson, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
            logger.info('Intermediate ipynb file has been saved.')

        self.result_preprocess = True  # TODO
        return self.result_preprocess

    def _process_cell_raw(self, cell_raw):
        md = ['\n', '```\n']
        md.extend(list(cell_raw['source']))
        md[-1] = md[-1] + '\n'
        md.extend(['```\n', '\n'])

        # folding
        is_source_hidden = cell_raw.get('metadata', {}).get('jupyter', {}).get('source_hidden', False)
        is_source_hidden = is_source_hidden and (self.args['folding_mode'] != 'ignore')
        if is_source_hidden:
            md = ['\n',
                  '<details>\n',
                  '<summary>hidden raw cell</summary>\n', '\n',
                  *md,
                  '\n', '</details>\n', '\n']

        return md

    def _process_cell_md(self, cell_md):
        md = ['\n']
        md.extend(list(cell_md['source']))
        md[-1] = md[-1] + '\n'
        md.extend(['\n'])

        # マークダウン中の $$~$$ を ```math~``` にする
        count_ddoller = 0
        for i in range(len(md)):
            if md[i] != '$$\n':
                continue

            count_ddoller += 1

            if count_ddoller % 2 == 1:
                md[i] = '```math\n'
            else:
                md[i] = '```\n'

        # マークダウン中の inline math を `\` でエスケープ
        is_display_math = False
        for i in range(len(md)):
            if md[i] == '```math\n':
                is_display_math = True
            elif md[i] == '```\n':
                is_display_math = False
            else:
                if is_display_math:
                    continue

                # find characters to be escaped
                lst = md[i].split('$')  # odd-index sring is inline math
                for j in range(len(lst) // 2):
                    idx = 2 * j + 1
                    lst[idx] = re.sub(r'\\\\', r'\\\\\\\\', lst[idx])  # '\\' -> '\\\\' (escaping line break)
                    lst[idx] = re.sub(r'(?<!\\)\\\s', r'\\\\ ', lst[idx])  # '\ ' -> '\\ ' (escaping hspace)
                    for c in ('_', ',', '!', '#', '%', '&', '{', '}'):  # '\%' -> '\\%' など
                        lst[idx] = re.sub(r'(?<!\\)\\{:s}'.format(c), r'\\\\{:s}'.format(c), lst[idx])
                    lst[idx] = re.sub(r'\*', r'\\ast', lst[idx])  # '*'   -> '\ast'
                    lst[idx] = re.sub(r"(?<!\^)'", r'^\\prime', lst[idx])  # "'"   -> '^\prime'
                    lst[idx] = re.sub(r'(?<!\\)_', '\\_', lst[idx])  # 'a_i' -> 'a\_i'

                md[i] = '$'.join(lst)

        # attachment があったら抽出
        at_images = {}  # key=attachment:(xxx.png), value=file path
        for at_name, v in cell_md.get('attachments', {}).items():
            path_at = self._save_encodedimage(v['image/png'])
            at_images[at_name] = path_at

        # attachment image を参照するimgタグがあったら抽出後のファイルパスで置き換え
        for i, l in enumerate(md):
            _l = l
            matches = list(re.finditer(r'!\[(.*?)\]\(attachment:(.+\.png)\)', l))
            for m in matches[::-1]:
                path_img = at_images.get(m.group(2), m.group(2))
                _l = _l[:m.start()] \
                    + '![%s](%s)' % (m.group(1), str(path_img)) \
                    + _l[m.end():]
            md[i] = _l

        # imgタグがあったらsha256からurlをゲットして、置き換え
        for i, l in enumerate(md):
            _l = l
            matches = list(re.finditer(r'!\[(.*?)\]\((.+\.png)\)', l))
            for m in matches[::-1]:
                fn = m.group(2)
                if len(fn) >= 4 and fn[:4] == 'http':
                    continue

                alttxt = m.group(1)
                path_img = self.path_root / Path(unquote(fn))
                try:
                    url = self._upload_image_and_get_url(path_img)
                except RuntimeError:
                    url = unquote(fn)
                    alttxt = alttxt + ' (upload failed)'

                _l = _l[:m.start()] \
                    + '![%s](%s)' % (alttxt, url) \
                    + _l[m.end():]
            md[i] = _l

        # folding
        is_source_hidden = cell_md.get('metadata', {}).get('jupyter', {}).get('source_hidden', False)
        is_source_hidden = is_source_hidden and (self.args['folding_mode'] != 'ignore')
        if is_source_hidden:
            md = ['\n',
                  '<details>\n',
                  '<summary>hidden markdown cell</summary>\n',
                  '\n',
                  *md,
                  '\n', '</details>\n', '\n']
        return md

    def _process_cell_code(self, cell_code):
        md_source = ['\n', '```{:s}\n'.format(self.language)]
        md_source.extend(list(cell_code['source']))
        md_source[-1] = md_source[-1] + '\n'
        md_source.extend(['```\n', '\n'])

        # source folding
        is_source_hidden = cell_code.get('metadata', {}).get('jupyter', {}).get('source_hidden', False)
        is_esapy_folded = any([self._includes_magic(l) for l in md_source])
        is_open = (self.args['folding_mode'] == 'ignore') \
            or not ((self.args['folding_mode'] == 'auto' and is_esapy_folded) or is_source_hidden)

        execution_count = cell_code.get('execution_count', 0)
        execution_count = execution_count if execution_count is not None else 0

        summary = 'code source (with %esapy_fold)' if is_esapy_folded else 'code source'

        md_source = ['\n',
                     '<details open>\n' if is_open else '<details>\n',
                     '<summary>[{:d}]: {:s}</summary>\n'.format(execution_count, summary),
                     '\n', *md_source, '\n', '</details>\n', '\n']

        # outputs
        func_dict = dict(stream=self._process_output_stream,
                         execute_result=self._process_output_result,
                         display_data=self._process_output_disp,
                         error=self._process_output_error)
        md_output = []
        for b in cell_code['outputs']:
            func = func_dict[b['output_type']]
            md_output.extend(func(b))

        # output scrolling
        is_scrolled = cell_code.get('metadata', {}).get('scrolled', False)
        if len(cell_code['outputs']) > 0 and is_scrolled:
            md_output.insert(0, '\n\n<div style="overflow: scroll; height: {:d}pt;">\n\n'.format(self.SCROLL_HEIGHT))
            md_output.append('\n\n</div>\n\n')

        # output folding
        if len(cell_code['outputs']) > 0:
            is_outputs_hidden = cell_code.get('metadata', {}).get('jupyter', {}).get('outputs_hidden', False)
            is_open = (self.args['folding_mode'] == 'ignore') or (not is_outputs_hidden)
            md_output = ['\n',
                         '<details open>\n' if is_open else '<details>\n',
                         '<summary>[{:d}]: outputs</summary>\n'.format(execution_count),
                         '\n', *md_output, '\n', '</details>\n', '\n']

        # length check
        if len(cell_code['source']) == 0:
            md_source = []
        if len(cell_code['outputs']) == 0:
            md_output = []

        # merge
        md = md_source + md_output

        return md

    def _process_output_stream(self, output_stream):
        txt = [self._remove_ansi(l) for l in list(output_stream['text'])]
        return ['\n', '```\n'] + txt + ['\n', '```\n', '\n']

    def _process_output_result(self, output_result):
        if 'text/html' in output_result['data']:
            md = ['\n', '\n'] + list(output_result['data']['text/html']) + ['\n', '\n']

        elif 'text/latex' in output_result['data']:
            md = []
            for i, line in enumerate(output_result['data']['text/latex']):
                line = re.sub(r'\\\\', r'\\cr', line)
                line = re.sub(r'\\begin{equation\*}', r'\n```math\n\\begin{equation*}', line)
                line = re.sub(r'\\end{equation\*}', r'\\end{equation*}\n```\n', line)
                md.append(line)

        else:  # text/plain
            md = ['\n', '```\n'] + list(output_result['data']['text/plain']) + ['\n', '```\n', '\n']

        return md

    def _process_output_disp(self, output_disp):
        md = []

        if 'image/png' in output_disp['data']:
            alttxt = ''.join(output_disp['data'].get('text/plain', ['']))
            path_img = self._save_encodedimage(output_disp['data']['image/png'])
            try:
                url = self._upload_image_and_get_url(path_img)
                md.append('![{:s}]({:s})\n'.format(alttxt, url))
            except RuntimeError:
                md.append('<img src="data:image/png;base64,{:s}">\n'.format(output_disp['data']['image/png']))

        else:
            md.append('![no image display_data output (unsupported)](error.png)')

        return md

    def _process_output_error(self, output_error):
        txt = [self._remove_ansi(l) + '\n' for l in list(output_error['traceback'])]
        return ['\n', '```\n'] + txt + ['```\n', '\n']

    def _upload_image_and_get_url(self, path_img):
        '''filepathからsha256を計算、ハッシュリストを参照してアップロード済みか確認する
        未アップならアップロードしてURLを返す
        アップ済みならURLを返す

        エラー処理は読み出しもとで行う
        '''
        d = self.nbjson['metadata']['esapy']['hashdict']
        h = self._get_sha256(path_img)

        if h not in d:  # unuploaded image
            url, _ = upload_binary(path_img,
                                   token=self.args['token'],
                                   team=self.args['team'],
                                   proxy=self.args['proxy'])
            d[h] = url  # record url and sha256

        return d[h]

    def _save_encodedimage(self, s_b64):
        '''base64-encoded-multiline-png-data を一時ファイルに保存して、ファイルパスを返す
        '''
        p = self._mkstemp(suffix='.png')
        with p.open('wb') as f:
            dat = base64.b64decode(s_b64)
            f.write(dat)
        return p

    def _mkstemp(self, **kwargs):
        '''一時ファイルを確保してファイルパスを返す
        '''
        args = dict(dict(dir=self.path_pwd), **kwargs)
        fd, fn_tmp = tempfile.mkstemp(**args)
        self._fd_list.append(fd)
        return Path(fn_tmp)

    def _get_sha256(self, path_file):
        '''指定したファイルのsha256を算出
        '''
        m = hashlib.sha256()
        with Path(path_file).open('rb') as f:
            m.update(f.read())
        return m.hexdigest()

    def upload_body(self):
        # load temp ipynb
        with self.path_ipynb.open('r', encoding='utf-8') as f:
            self.nbjson = json.load(f)

        # load temp md
        with self.path_md.open('r', encoding='utf-8') as f:
            md_body = f.readlines()
            md_body = ''.join(md_body)

        logger.info('Gathering information for create post')
        info_dict = self.gather_post_info()
        logger.debug(info_dict)

        # upload ipynb itself and insert link
        try:
            ipynb_url, _ = upload_binary(self.path_input,
                                         token=self.args['token'],
                                         team=self.args['team'],
                                         proxy=self.args['proxy'])

            s_link = 'ipynb file -> [{:s}]({:s})\n\n'.format(str(self.path_input), ipynb_url)
            md_body = s_link + md_body
        except RuntimeError as e:
            logger.warn('uploading ipynb file itself failed.')

        # insert warning for local edit
        msg_warnforedit = '<!-- This markdown text was automatically generated by esapy. You should not edit this. Please edit the original ipynb and upload again. -->\n'
        msg_warnforedit += '<!-- このテキストは jupyter notebook から自動生成されたものです。このテキストを直接編集することは避け、元のipynbファイルを編集した後に再度アップロードしてください。 -->\n\n\n'
        md_body = msg_warnforedit + md_body

        # post / patch
        post_number = self.get_post_number()
        if post_number is None or self.args['post_mode'] == 'new':
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
        self.nbjson['metadata']['esapy']['post_info'] = self.post_info
        self.nbjson['metadata']['esapy']['post_info'].pop('body_html')  # clear body, because body is generally large but didn't be used,
        self.nbjson['metadata']['esapy']['post_info'].pop('body_md')
        self.result_upload = self.is_uploaded()

        with self.path_ipynb.open('w', encoding='utf-8') as f:
            json.dump(self.nbjson, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
            logger.info('Intermediate ipynb file has been saved.')

        return post_url

    def save(self):
        '''動作モードに応じて出力されたmdファイルを保存する
        '''
        with self.path_ipynb.open('r', encoding='utf-8') as f:
            ipynb_json = json.load(f)

        # record version
        ipynb_json['metadata']['esapy']['version'] = get_version()

        if self.args['output'] is not None:
            # output が指定されている
            p = Path(self.args['output'])
            logger.info('output file path={:s}'.format(str(p)))
            with p.open('w', encoding='utf-8') as f:
                json.dump(ipynb_json, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

        elif self.args['destructive']:
            p = self.path_input
            logger.info('output file path={:s}'.format(str(p)))
            with p.open('w', encoding='utf-8') as f:
                json.dump(ipynb_json, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

        else:
            logger.info('no-output mode')

    def get_post_number(self):
        try:
            return self.nbjson['metadata']['esapy']['post_info']['number']
        except KeyError:
            return None

    def is_uploaded(self):
        return self.get_post_number() is not None

    def gather_post_info(self):
        '''gathering informatin for create/update post
        '''
        info_prev_metadata = self.nbjson['metadata']['esapy']['post_info']  # post_info written in metadata
        number = info_prev_metadata['number']
        info_prev = {}
        if number is not None:
            logger.info('post_number is not None. -> checking post/{:d} ...'.format(number))
            try:
                info_prev = get_post(number,
                                     token=self.args['token'],
                                     team=self.args['team'],
                                     proxy=self.args['proxy'])
                logger.info('getting post/{:d} was succeeded.'.format(number))
            except RuntimeError as e:
                logger.info('getting post/{:d} was failed. -> clearing post_number to set as None.'.format(number))
                info_prev = info_prev_metadata
                info_prev['number'] = None
        else:
            info_prev = info_prev_metadata
        logger.info('info_prev has been gathered.')
        logger.debug(info_prev)
        d = {}  # dict to return

        # manage tags (None or list)
        tags = info_prev.get('tags', '')
        if isinstance(tags, list):
            d['tags'] = tags
        elif tags is not None:
            d['tags'] = tags.split(', ')
        else:
            d['tags'] = []

        if self.args['tags'] is not None:
            d['tags'].extend(self.args['tags'])
        d['tags'] = list(set(d['tags']))  # unique

        # wip (bool)
        d['wip'] = not (not self.args['wip'] or not info_prev.get('wip', True))

        # category, name (None or str)
        for k in ['category', 'message', 'name']:
            if self.args[k] is not None:
                d[k] = self.args[k]
            else:
                d[k] = info_prev.get(k, None)

        # message (None or str)
        d['message'] = self.args['message'] if 'message' in self.args else None

        return d

    def _remove_ansi(self, s):
        return re.sub(r'\x1b[^m]*m', '', s)

    def _includes_magic(self, l):
        m = re.search(r'%esapy_fold', l)
        if m is None:
            return False

        if re.search('#', l[:m.start()]) is None:
            return True
        else:
            return False
