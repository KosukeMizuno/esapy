# esapy

A python implementation of esa.io API

The main purpose of this package is implementation of easy uploading and sharing jupyter notebook to esa.io service.


[![PyPI version](https://badge.fury.io/py/esapy.svg)](https://badge.fury.io/py/esapy) [![Python Versions](https://img.shields.io/pypi/pyversions/esapy.svg)](https://pypi.org/project/esapy/)
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

Description in Japanese: <https://esa-pages.io/p/sharing/14661/posts/184/d983bd2e71ad35528500.html>


## INSTALATION

1. Install package

    ```shell
    $pip install esapy
    ```

1. set credentials (for esa.io)
  1. generate esa.io token with read/write permission.
  1. make configuration in your environment variables
      Environment variables: `ESA_PYTHON_TOKEN`, `ESA_PYTHON_TEAM`.
      You can check your token using `esa config` from command line. 

1. set credentials (for growi)
  1. generate token
  1. set environment variables
    - `GROWI_URL`
    - `GROWI_TOKEN`


## HOW TO USE

1. Prepare .ipynb file

1. Upload your notebook

    ```shell
    $ esa up target.ipynb
    ```

    This package uploads images, and uploads markdown file as a new post or update the previously uploaded post.

1. access the new post and edit.

If process fails due to a network problem, you can check by `esa stats`.

Whether an ipynb file has been already uploaded can be checked by `esa ls <filepath or dirpath>`.
For list up all notebooks recursively, `esa ls --recursive`.

## DOCUMENT

### commands

This package registers following command line tools.

- `esa up <input_filepath>`
  - upload your file
  - supported format: ipynb, tex, and md

- `esa config`
  - list environs and config

- `esa stats`
  - show statistics of your team
  - This command can be used for access test.

- `esa reset <target.ipynb> [--number <post_number>]`
  - remove upload history by esapy in notebook file
  - new post_number can be assigned

- `esa ls <dirname or filepath>`
  - show notebook list in the directory
  - `<dirname>` can be abbreveated. Default is the current working directory.

### (deprecated) config file

Use environment variable instead of config file.

The config file (`~/.esapyrc`) should be written in yaml format.
An example is shown below.

```yaml: ~/.esapyrc
token: your_token
team: your_team
```

### TIPS

Combination with fuzzy finders like [fzf](https://github.com/junegunn/fzf) is useful.
For example,

```sh: ~/.bashrc
alias esafu='esa up --no-browser "$(esa ls | fzf | sed -r "s/(.+)\\| (.+)/\\2/")"'
```

## INSTALLATION for DEVELOPMENT

1. setup poetry on your environment
1. clone this repository
1. cd repo directory
1. `poetry install`
1. `git checkout develop`


## For Growi adminitorator

Allow `details` tag and `open` attribute by configuration.
Allow guest user access by security configuration. Some APIs have bug related to authentication.


## LICENSE

Copyright (c) 2020 Kosuke Mizuno  
This package is released under the MIT license (see [LICENSE](LICENSE) file).
