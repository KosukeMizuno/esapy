#!/usr/bin/env python3

import os
from pathlib import Path
import mimetypes
import requests
import json
import uuid
import hashlib

# logger
from logging import getLogger
logger = getLogger(__name__)


def _set_proxy(proxy):
    if proxy is None:
        logger.debug('No proxy is addressed.')
        return

    logger.info('Addressed proxy: %s' % proxy)
    os.environ['HTTP_PROXY'] = proxy
    logger.debug('HTTP_PROXY={:s}'.format(os.environ['HTTP_PROXY']))
    os.environ['HTTPS_PROXY'] = proxy
    logger.debug('HTTPS_PROXY={:s}'.format(os.environ['HTTPS_PROXY']))


def get_team_stats(token=None, url=None, proxy=None):
    logger.info('Getting healthcheck of growi')

    _set_proxy(proxy)

    # get metadata
    payload = {'access_token': token,
               'checkServices': ['mongo', 'search'],
               'strictly': True}

    res = requests.get(url + '/healthcheck', data=json.dumps(payload))
    logger.debug(res)
    logger.debug(res.headers)
    if res.status_code == 200:
        logger.info('healthy')
        print('growi system is healthy')
    elif res.status_code == 503:
        logger.warning('unhealty')
    else:
        raise RuntimeError('Getting team statistics failed.')
    logger.debug(res.text)

    return res.text


def upload_binary(filename, token=None, url=None, proxy=None):
    path_bin = Path(filename)
    logger.info('Uploading binary data, path=%s' % str(path_bin))
    logger.info('  filesize: %d' % path_bin.stat().st_size)

    _set_proxy(proxy)
    payload = {'access_token': token}

    # upload file
    logger.info('Posting binary...')
    with path_bin.open('rb') as imgfile:
        payload['file'] = imgfile
        res = requests.post(url + '/attachments.add', data=payload)

    if res.status_code != 200:
        logger.warning('Upload failed, %s' % str(path_bin))
        raise RuntimeError('Upload failed.')

    image_url = res.json()['attachment']['filePathProxied']
    logger.info('The file has been uploaded successfully, url: %s' % image_url)

    return image_url, res


def get_post(page_id, token=None, url=None, proxy=None):
    logger.info('Getting post/{:d}'.format(page_id))

    # post
    _set_proxy(proxy)
    payload = {'access_token': token,
               'page_id': page_id,
               }

    res = requests.post(url + '/pages.get',
                        data=json.dumps(payload))
    logger.debug(res)

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
               'path': '/user/bot/' + name,
               'grant': 1  # なにこれ？ とりあえず1にしておいたけどドキュメントがない
               }

    res = requests.post(url + '/create',
                        data=json.dumps(payload))
    logger.debug(res)

    if res.status_code == 409:
        raise RuntimeError('Page path is already existed. Retry with different name.')
    elif res.status_code != 201:
        raise RuntimeError('Create post failed.')
    logger.info('New post was successfully created.')

    d = res.json()
    logger.debug(d['page'])
    pageurl = url + '/' + d['page']['path']
    logger.info('URL of the created post: %s' % pageurl)

    return pageurl, res


def patch_post(page_id, body_md, token=None, url=None, proxy=None):
    logger.info('Updating post')

    # post
    _set_proxy(proxy)
    rev = hashlib.sha256(uuid.uuid4()).hexdigest()
    payload = {'access_token': token,
               'body': body_md,
               'page_id': page_id,
               'revision_id': rev,
               'grant': 1  # なにこれ？ とりあえず1にしておいたけどドキュメントがない
               }

    res = requests.post(url + '/pages.update',
                        data=json.dumps(payload))
    logger.debug(res)

    if res.status_code != 200:
        raise RuntimeError('Create post failed.')
    logger.info('New post was successfully created.')

    d = res.json()
    logger.debug(d['page'])
    pageurl = url + '/' + d['page']['path']
    logger.info('URL of the created post: %s' % pageurl)

    return pageurl, res
