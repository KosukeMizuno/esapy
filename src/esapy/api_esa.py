#!/usr/bin/env python3

import os
from pathlib import Path
import mimetypes
import requests
import json

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


def get_team_stats(token=None, team=None, proxy=None):
    logger.info('Getting team statistics')

    _set_proxy(proxy)

    # get metadata
    url = 'https://api.esa.io/v1/teams/%s/stats' % team
    header = dict(Authorization='Bearer %s' % token)

    res = requests.get(url, headers=header)
    if res.status_code != 200:
        logger.warning('Getting team statistics failed.')
        raise RuntimeError('Getting team statistics failed.')
    logger.debug(res)

    d = res.json()
    logger.debug(d)
    return d


def upload_binary(filename, token=None, team=None, proxy=None):
    path_bin = Path(filename)
    logger.info('Uploading binary data, path=%s' % str(path_bin))
    logger.info('  filesize: %d' % path_bin.stat().st_size)

    _set_proxy(proxy)

    # get metadata
    logger.info('Obtaining metadata for upload...')
    url = 'https://api.esa.io/v1/teams/%s/attachments/policies' % team
    header = dict(Authorization='Bearer %s' % token)
    mtype = mimetypes.guess_type(str(path_bin))[0]
    mtype = mtype if mtype is not None else 'application/octet-stream'
    params = dict(type=mtype,
                  name=path_bin.name,
                  size=path_bin.stat().st_size)
    res = requests.post(url, headers=header, params=params)

    if res.status_code != 200:
        logger.warning('Obtaining metadata failed, %s' % str(path_bin))
        raise RuntimeError('Obtaining metadata failed.')

    metadata = res.json()
    image_url = metadata['attachment']['url']

    logger.info('  finished.')
    logger.debug(metadata)

    # upload file
    logger.info('Posting binary...')
    url = metadata['attachment']['endpoint']
    with path_bin.open('rb') as imgfile:
        params = metadata['form']
        params['file'] = imgfile
        res = requests.post(url, files=params)

    if not (200 <= res.status_code < 300):
        logger.warning('Upload failed, %s' % str(path_bin))
        raise RuntimeError('Upload failed.')
    logger.info('The file has been uploaded successfully, url: %s' % image_url)

    return image_url, res


def get_post(post_number, token=None, team=None, proxy=None):
    logger.info('Getting post/{:d}'.format(post_number))

    _set_proxy(proxy)

    # get metadata
    url = 'https://api.esa.io/v1/teams/{:s}/posts/{:d}'.format(team, post_number)
    header = dict(Authorization='Bearer {:s}'.format(token))

    res = requests.get(url, headers=header)
    if res.status_code != 200:
        logger.warning('Getting post failed.')
        raise RuntimeError('Getting post failed.')
    logger.info(res)

    d = res.json()
    logger.debug(d)

    return d


def create_post(body_md, token=None, team=None, name=None, tags=None, category=None, wip=True, message=None, proxy=None):
    logger.info('Creating new post')

    # post
    _set_proxy(proxy)
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
    logger.info('URL of the created post: %s' % d['url'])

    return d['url'], res


def patch_post(post_number, body_md, token=None, team=None, name=None, tags=None, category=None, wip=True, message=None, proxy=None):
    logger.info('Updating post/{:d}'.format(post_number))

    # post
    _set_proxy(proxy)
    url = 'https://api.esa.io/v1/teams/{:s}/posts/{:d}'.format(team, post_number)
    header = {'Authorization': 'Bearer {:s}'.format(token),
              'Content-Type': 'application/json'}

    params = dict(post=dict(name=name or "",
                            message=message or "Update post via esapy",
                            body_md=body_md,
                            wip=wip))
    if len(params['post']['name']) > 0 and params['post']['name'][0] != '/':
        params['post']['name'] = '/' + params['post']['name']
    if isinstance(tags, list) and all([isinstance(t, str) for t in tags]):
        params['post']['tags'] = tags
    if category is not None:
        params['post']['category'] = category

    res = requests.patch(url, headers=header, data=json.dumps(params))
    logger.debug(res)

    if res.status_code != 200:
        print(res)
        print(res.json())
        raise RuntimeError('Create post failed.')
    logger.info('Patching post was successfully created.')

    d = res.json()
    logger.debug(dict(d, **{'body_md': '<not shown>', 'body_html': '<not shown>'}))
    logger.info('URL of the created post: %s' % d['url'])

    if d['overlapped']:
        logger.warning('!!! 3 way merge and conflicting has been occured !!!')

    return d['url'], res
