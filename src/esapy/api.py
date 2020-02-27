#!/usr/bin/env python3

import os
from pathlib import Path
import mimetypes
import requests
import json

# logger
from logging import getLogger


def _set_proxy(proxy, logger=None):
    logger = logger or getLogger(__name__)

    if proxy is None:
        return

    logger.info('proxy: %s' % proxy)
    os.environ['HTTP_PROXY'] = proxy
    os.environ['HTTPS_PROXY'] = proxy


def get_team_stats(token=None, team=None, proxy=None, logger=None):
    logger = logger or getLogger(__name__)

    logger.info('getting team statistics')

    _set_proxy(proxy, logger=logger)

    # get metadata
    url = 'https://api.esa.io/v1/teams/%s/stats' % team
    header = dict(Authorization='Bearer %s' % token)

    res = requests.get(url, headers=header)
    logger.info(res)

    d = res.json()

    print(d)
    return d


def upload_binary(filename, token=None, team=None, proxy=None, logger=None):
    logger = logger or getLogger(__name__)

    path_bin = Path(filename)
    logger.info('uploading binary, %s' % str(path_bin))
    logger.info('  filesize: %d' % path_bin.stat().st_size)

    _set_proxy(proxy, logger=logger)

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


def create_post(body_md, token=None, team=None, name=None, tags=None, category=None, wip=True, message=None, proxy=None, logger=None):
    logger = logger or getLogger(__name__)

    logger.info('uploading markdown')

    # post
    _set_proxy(proxy, logger=logger)
    url = 'https://api.esa.io/v1/teams/%s/posts' % team
    header = {'Authorization': 'Bearer %s' % token,
              'Content-Type': 'application/json'}

    params = dict(post=dict(name=name or "",
                            message=message or "Create post via esapy",
                            body_md=body_md,
                            wip=wip))
    if isinstance(tags, list) and all([isinstance(t, str) for t in tags]):
        params['post']['tags'] = tags
    if category is not None:
        params['post']['category'] = category

    res = requests.post(url, headers=header, data=json.dumps(params))
    logger.debug(res)

    if res.status_code != 201:
        raise RuntimeError('Create post failed.')
    logger.info('New post was successfully created.')

    d = res.json()
    logger.debug(dict(d, **{'body_md': '<not shown>', 'body_html': '<not shown>'}))
    print('New post was created, url: %s' % d['url'])

    return d['url']


if __name__ == '__main__':
    pass
