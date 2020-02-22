#!/usr/bin/env python3

import sys
import os
import re
import subprocess
from pathlib import Path
import tempfile
import mimetypes
from urllib.parse import quote

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


def upload_ipynb(filename, token=None, team=None, use_tmp_folder=False, logger=None):
    """
    1) Convert ipynb file to markdown and generate images.
    2) Upload images.
    3) Generate markdown with uploaded-urls.

    4*) Replace latex code blocks ($$~$$) to math code blocks (```math ~ ```).
    5*) Upload markdown as a new post.
    Stared features have not been implemented.

    Parameters
    ----------
    filename: str
        filename of the target jpyter notebook (.ipynb).
    token: str
        access token of esa.io
    team: str
        name of your team
    use_temp_folder: bool, dafult=False
        If False, .md file and images will be generated at same place of the target ipynb file.

    """
    logger = logger or default_logger

    path_ipynb = Path(filename)
    logger.info('starting esapy#upload')
    logger.info('file: %s' % str(path_ipynb))

    #### file check ####
    if not path_ipynb.suffix == '.ipynb':
        raise RuntimeError('The assigned file (%s) is not a jupyter notebook.' % str(path_ipynb))

    ####
    with tempfile.TemporaryDirectory() as dname:
        # set working directory
        if use_tmp_folder:
            logger.info('temporary directory: %s' % str(dname))
            path_wd = Path(dname)
        else:
            path_wd = path_ipynb.parent

        # process
        logger.info('calling nbconvert')
        cmd = ['jupyter', 'nbconvert',
               '--to=markdown']

        cmd.append('--output-dir=%s' % str(path_wd))
        cmd.append(str(path_ipynb))
        subprocess.check_call(cmd)

        path_md = path_wd / (path_ipynb.stem + '.md')
        path_list_img = list(path_wd.glob('%s_files/*.png' % path_ipynb.stem))

        logger.info('generated markdown: %s' % str(path_md))
        logger.info('%d images were generated:' % len(path_list_img))
        for p in path_list_img:
            logger.info('  %s' % str(p))

        # upload images & make replace list
        logger.info('uploading images...')
        replace_list = []  # png filename, path obj, url
        for p in path_list_img:
            url = upload_binary(p, token=token, team=team)
            # import uuid  # テスト用
            # url = str(uuid.uuid4())  # テスト用
            replace_list.append((quote(p.stem), p, url))
        replace_list_index = [x[0] for x in replace_list]
        for fn, p, url in replace_list:
            logger.info('  %s -> %s' % (fn, url))
        logger.info('%d files were uploaded.' % len(replace_list))

        # replace image url
        # example ==> '![png](gaussian%20beam_files/gaussian%20beam_10_0.png)\n'
        logger.info('replacing image urls...')
        md_body = path_md.open('r').readlines()
        md_body_replaced = []
        n = 0
        for i, l in enumerate(md_body):
            if not (l[0] == '!'):
                md_body_replaced.append(l)
                continue

            m = re.match(r'!\[(.+)\]\((.+)/(.+)(\..+)\)\n', l)
            if m is not None:
                logger.info('line %d, "%s"' % (i, l.strip()))

                # find url
                fn = m.group(3)
                url = replace_list[replace_list_index.index(fn)][2]

                # replace
                _l = '![%s](%s)\n' % (m.group(3), url)
                md_body_replaced.append(_l)
                n += 1
                logger.info('       -> "%s"' % _l.strip())
        logger.info('%d urls were replaced.' % n)

        # replace math codeblock
        pass

        # upload markdownw
        path_md.open('w').writelines(md_body_replaced)
        logger.info('markdown file with replaced image-urls was generated.')


def upload_md(filename, token=None, team=None, name=None, tags=None, category=None, wip=True, message=None, logger=None):
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


def upload_binary(filename, token=None, team=None, logger=None):
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
    pass
