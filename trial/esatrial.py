#!/usr/bin/env python3

import yaml
import requests
from pprint import pprint
from pathlib import Path

if __name__ == '__main__':
    token = 'XXXXX'
    team_name = 'YYYYYY'

    # TEST, GET statistics
    #url = 'https://api.esa.io/v1/teams/%s/stats' % team_name
    #h = dict(Authorization='Bearer %s' % token)
    #res = requests.get(url, headers=h)
    #pprint(res.json())
    #print(res)

    # TEST, UPLOAD
    # 1: get metadata
    ##fn = '/mnt/c/Users/MIZUNO/Desktop/neko.png'
    fn = '/mnt/c/Users/MIZUNO/Desktop/34679-7-maneki-neko.png'
    path_png = Path(fn)
    print('filecheck ==>', path_png.exists())
    print('filesize:', path_png.stat().st_size)

    url = 'https://api.esa.io/v1/teams/%s/attachments/policies' % team_name
    h = dict(Authorization='Bearer %s' % token)
    d = dict(type='image/png',
             name=path_png.name,
             size=path_png.stat().st_size)
    res = requests.post(url, headers=h, params=d)
    metadata = res.json()
    pprint(res.json())
    print(res)

    print(res.json().__class__)

    # 2: upload png file
    url = metadata['attachment']['endpoint']
    url_image = metadata['attachment']['url']

    params = metadata['form']
    with path_png.open('rb') as imgfile:
        # params['Content-Type'] = 'multipart/form-data'
        # files = dict(file=imgfile)
        params['file'] = imgfile
        
        print('@@@@@@@@@@@')
        pprint(params)
        print('@@@@@@@@@@@ @')
        res = requests.post(url, files=params)#, params=params, files=files)

    print(res)
    print(res.content)
    pprint(res.json())
    print(res)

    pass
