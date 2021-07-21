#!/usr/bin/env python3

import os
from pathlib import Path
import mimetypes
import requests
import json
import uuid
from urllib.parse import quote
import hashlib

# logger
from logging import getLogger
logger = getLogger(__name__)

from .loadrc import KEY_GROWI_USERNAME


def _set_proxy(proxy):
    if proxy is None:
        logger.debug('No proxy is addressed.')
        return

    logger.info('Addressed proxy: %s' % proxy)
    os.environ['HTTP_PROXY'] = proxy
    logger.debug('HTTP_PROXY={:s}'.format(os.environ['HTTP_PROXY']))
    os.environ['HTTPS_PROXY'] = proxy
    logger.debug('HTTPS_PROXY={:s}'.format(os.environ['HTTPS_PROXY']))


def _get_growi_username():
    return os.environ[KEY_GROWI_USERNAME]


def get_team_stats(token=None, url=None, proxy=None):
    logger.info('Getting healthcheck of growi')

    _set_proxy(proxy)

    # get metadata
    res = requests.get(url + '/_api/v3/statistics/user',
                       params=dict(access_token=token))
    logger.debug(res)
    logger.debug(res.headers)
    if res.status_code == 200:
        pass
    else:
        raise RuntimeError('Getting team statistics failed.')
    print(res.json())

    return res.json()


def upload_binary(filename, token=None, url=None, proxy=None):
    path_bin = Path(filename)
    logger.info('Uploading binary data, path=%s' % str(path_bin))
    logger.info('  filesize: %d' % path_bin.stat().st_size)

    _set_proxy(proxy)

    page_id = get_post_by_path('/user/' + _get_growi_username(), token, url, proxy)['_id']

    # upload file
    logger.info('Posting binary...')
    with path_bin.open('rb') as imgfile:
        res = requests.post(url + '/_api/attachments.add',
                            data=dict(page_id=page_id,
                                      access_token=token),
                            files=dict(file=(path_bin.name,
                                             imgfile,
                                             mimetypes.guess_type(path_bin)[0]))
                            )
    logger.debug(res.headers)

    if res.status_code != 200:
        logger.warning('Upload failed, %s' % str(path_bin))
        raise RuntimeError('Upload failed.')

    image_url = res.json()['attachment']['filePathProxied']
    logger.info('The file has been uploaded successfully, url: %s' % image_url)

    return image_url, res


def get_post(page_id, token=None, url=None, proxy=None):
    logger.info('Getting post/{:}'.format(page_id))

    # post
    _set_proxy(proxy)
    payload = {'access_token': token,
               'page_id': page_id}
    res = requests.get(url + '/_api/pages.get',
                       params=payload)
    logger.debug(res)

    if res.status_code != 200:
        logger.warning('Getting post failed.')
        raise RuntimeError('Getting post failed.')

    d = res.json()
    logger.debug(d)

    return d['page']


def get_post_by_path(pagepath, token=None, url=None, proxy=None):
    logger.info('Getting post/{:}'.format(pagepath))

    _set_proxy(proxy)

    payload = {'access_token': token,
               'path': pagepath}
    res = requests.get(url + '/_api/pages.get',
                       params=payload)
    logger.debug(res)
    logger.debug(res.headers)
    # logger.debug(res.text)

    if res.status_code != 200:
        logger.warning('Getting post failed.')
        raise RuntimeError('Getting post failed.')

    d = res.json()
    logger.debug(d)

    return d['page']


def create_post(body_md, token=None, url=None, name=None, proxy=None):
    logger.info('Creating new post')

    # post
    _set_proxy(proxy)

    if name is None:
        raise RuntimeError('`name` is required.')

    payload = {'access_token': token,
               'body': body_md,
               'path': '/user/' + _get_growi_username() + '/' + name}
    res = requests.post(url + '/_api/v3/pages/',
                        data=payload)
    logger.debug(res)
    logger.debug(res.headers)

    if res.status_code == 409:
        raise RuntimeError('Page path is already existed. Retry with different name.')
    elif res.status_code != 201:
        raise RuntimeError('Create post failed.')
    logger.info('New post was successfully created.')

    d = res.json()
    logger.debug(d['data']['page'])
    pageurl = url + '/' + d['data']['page']['path']
    logger.info('URL of the created post: %s' % pageurl)

    return pageurl, res


def patch_post(page_id, body_md, name, token=None, url=None, proxy=None):
    logger.info('Updating post: {:}'.format(page_id))

    page_dat = get_post(page_id, token, url, proxy)

    # post
    _set_proxy(proxy)
    payload = {'body': body_md,
               'page_id': page_id,
               'revision_id': page_dat['revision']['_id']
               }
    logger.debug(payload)
    res = requests.post(url + f'/_api/pages.update?access_token={quote(token)}',
                        data=payload,
                        )
    logger.debug(res)

    if res.status_code != 200:
        raise RuntimeError('Create post failed.')

    d = res.json()
    logger.debug(d)
    logger.debug(d['page'])
    pageurl = url + '/' + d['page']['path']

    logger.info('New post was successfully created.')
    logger.info('URL of the created post: %s' % pageurl)
    return pageurl, res
