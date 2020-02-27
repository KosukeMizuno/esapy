# esapy

A python implementation of esa.io API

The main purpose of this package is implementation of easy uploading and sharing jupyter notebook to esa.io service.


[![PyPI version](https://badge.fury.io/py/esapy.svg)](https://badge.fury.io/py/esapy) [![Python Versions](https://img.shields.io/pypi/pyversions/esapy.svg)](https://pypi.org/project/esapy/)
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)


## INSTALATION

1. Install pandoc

    ```shell
    $ sudo apt install pandoc
    ```
    
    This package call nbconvert internally.

1. Install package

    ```shell
    $ pip install esapy
    ```

1. generate esa.io token with read/write permission.

1. make configuration file in your home directory (`~/.esapyrc`).

    ```YAML: ~/.esapyrc
    token: your_token
    team: your_team
    ```

    - You can set them as environment variables: `ESA_PYTHON_TOKEN`, `ESA_PYTHON_TEAM`.
    - Environment variables are prior to `.esapyrc` file.
    - You can check your token using `esa config` from command line. 



## HOW TO USE

1. Prepare .ipynb file

1. Convert to markdown and upload images.

    ```shell
    $ esa up target.ipynb
    ```

    This package will call nbconvert and upload images, and upload markdown file as new post.

1. access the new post and edit.

1. if process fails due to a network problem, you can re-try with `esa up target.md` .  When the input is a markdown, `nbconvert` step will be skipped.


## DOCUMENT

### commands
This package registers following command line tools.
- `esa up <input_filepath>`
  - upload your file
  - supported format: ipynb, tex, and md
  - This command calls `esa convert` , `esa replace` , and `esa publish` internally

- `esa config`
  - list environs and config

- `esa stats`
  - show statistics of your team
  - This command can be used for access test.

- `esa convert <input_filepath>`
  - subcommand
  - call nbconvert or pandoc depending input format

- `esa replace <input_filepath markdown file>`
  - subcommand
  - scan lines of markdown finding image tags (`![xxx](yyy)`).
  - when the file path is not url, image file will be uploaded to your team of esa.io.
  - If token/team are given as arguments and config file simultaneously, arguments are used.

- `esa publish <input_filepath markdown file>`
  - subcommand
  - create new post


### config file
The config file (`~/.esapyrc`) should be written in yaml format.
An example is shown below.
```yaml: ~/.esapyrc
token: your_token
team: your_team

action:
  goto_clipboard: true
```

If `action.goto_clipboard` is true, a markdown body with modified urls will be copied to clipboard.  Default is false.

## License
Copyright (c) 2020 Kosuke Mizuno  
This package is released under the MIT license (see [LICENSE](LICENSE) file).
