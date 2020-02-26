#!/usr/bin/env python3

from pathlib import Path
import mimetypes
import requests


# logger
from logging import getLogger


def upload_binary(filename, token=None, team=None, proxy=None, logger=None):
    if proxy is not None:
        raise RuntimeError('proxy has not yet been implemented.')

    logger = logger or getLogger(__name__)

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
