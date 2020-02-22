#!/usr/bin/env python3

import sys
from pathlib import Path
from .loadrc import get_token_and_team
from .upload import upload_ipynb


def main():
    p = Path(sys.argv[1])

    token, team = get_token_and_team()
    upload_ipynb(p, token=token, team=team)


if __name__ == '__main__':
    main()
