
from esapy.api_growi import create_post
from esapy.loadrc import get_token_and_team
from esapy.entrypoint import parser


def test_create_post():
    args = parser.parse_args([])
    token, url, dest = get_token_and_team(args)
    assert dest == 'growi'

    body_md = '''
    # test markdown
    aaa

    ## h2 test
    xxxx

    <https://google.com/>
    '''

    pageurl, res = create_post(body_md,
                               token=token, url=url, name='test',
                               proxy=None)
