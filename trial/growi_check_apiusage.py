#!/usr/bin/env python3

import sys
from pprint import pprint
import mimetypes
from pathlib import Path
import requests
from urllib.parse import quote
import json
import os
import uuid

import logging
logging.getLogger('urllib').setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.DEBUG)

URL = os.environ['GROWI_URL']
TOKEN = os.environ['GROWI_TOKEN']


if False:
    api_key = {'access_token': TOKEN}
    api_key_url = 'access_token=' + TOKEN

    # これは200だしjsonでかえってくる
    res = requests.get(URL + '/_api/v3/healthcheck',
                       params=api_key)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    # これは200だしjsonでかえってくる
    res = requests.get(URL + '/_api/v3/statistics/user',
                       params=api_key)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    # recentはaccess_tokenを無視するバグがある
    # https://github.com/weseek/growi/blob/226f33836bbba96e80b45280e445231568f9f17a/src/server/routes/apiv3/pages.js#L286
    # p = dict(access_token=TOKEN)
    # res = requests.get(URL + '/_api/v3/pages/recent', params=p)
    # print(res.url)
    # print(res.headers)
    # print(res.text)
    # assert res.status_code == 200
    # print(res.json())
    # print()

    p = dict(access_token=TOKEN, path='/')
    res = requests.get(URL + '/_api/v3/pages/list', params=p)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    # Note: curl -X POST -F "file=@trial/uploadtest.jpg" -F "path=/" -v "http://localhost:3000/_api/attachments.add?access_token=$(urlencode $GROWI_TOKEN)"
    fn = Path('trial/uploadtest.jpg')
    with fn.open('rb') as f:
        res = requests.post(URL + f'/_api/attachments.add',
                            files=dict(file=f),
                            data=dict(path='/' + str(uuid.uuid4()),
                                      access_token=TOKEN))
    print(res)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    p = dict(access_token=TOKEN,
             path='/')
    res = requests.get(URL + '/_api/pages.get', params=p)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    p = dict(access_token=TOKEN)
    res = requests.get(URL + '/_api/attachments.limit', params=p)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()


if True:
    # 記事を作成→取得→更新

    # # pages.create は移動されてる
    # md_body = '''# H1
    # aaa
    #
    # # bbbb
    # agrweg
    # '''
    # path = '/' + str(uuid.uuid4())
    # res = requests.post(URL + '/_api/v3/pages/',
    #                     data=dict(access_token=TOKEN,
    #                               body=md_body,
    #                               path=path)
    #                     )
    # print(res.url)
    # print(res.headers)
    # assert res.status_code == 201
    # pprint(res.json())
    # print()
    # page_id = res['data']['pages']['_id']
    page_id = '60f814a24ac3b7004a0960c5'

    p = dict(acces_token=TOKEN, page_id=page_id)
    res = requests.get(URL + '/_api/pages.get',
                       params=p)
    print(res)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    pprint(res.json())
    print()
    rev_id = res.json()['page']['revision']['_id']

    md_body_update = '''# H1
    aaa

    # bbbb
    agrweg

    Equation: $E=mc^2$
    '''
    p = dict(body=md_body_update,
             page_id=page_id,
             revision_id=rev_id)  # よくわからんけど最新のページのrevision_idを設定したらうまくいく（Undo treeみたいな構造をもっているのか？）
    res = requests.post(URL + f'/_api/pages.update?access_token={quote(TOKEN)}',
                        data=p)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    print(res.json())
    print()

    # Note: curl -X POST -F "file=@trial/uploadtest.jpg" -F "path=/" -v "http://localhost:3000/_api/attachments.add?access_token=$(urlencode $GROWI_TOKEN)"
    fn = Path('trial/uploadtest.jpg')
    with fn.open('rb') as f:
        mime = mimetypes.guess_type(fn)
        p = dict(file=(fn.name, f, mime[0]))
        res = requests.post(URL + '/_api/attachments.add',
                            files=p,
                            data=dict(page_id=page_id,
                                      access_token=TOKEN))
    print(res)
    print(res.url)
    print(res.headers)
    assert res.status_code == 200
    pprint(res.json())
    print()


if __name__ == '__main__':
    pass
