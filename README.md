# esapy

A python implementation of esa.io API

The main purpose of this package is implementation of easy uploading and sharing jupyter notebook to esa.io service.



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

1. make configuration file in your home directory (~/.esapyrc).

    ```YAML: ~/.esapyrc
    token: your_token
    team: your_team
    ```

    - You can set them as environment variables: ESA_PYTHON_TOKEN, ESA_PYTHON_TEAM.
    - Environment variables are prior to .esapyrc file.
    - You can check your token using `esa-token`. 



## HOW TO USE

1. Prepare .ipynb file

1. Convert to markdown and upload images.

    ```shell
    $ esa-up target.ipynb
    ```

    This package (for now) will call nbconvert and upload images, and will not upload markdown file as new post.

1. Post a new article by copy-and-paste the generated markdown file.


## DOCUMENT

### commands
This package registers following cli commands.
- esa-up <target.ipynb>
  - upload your notebook
- jupyter-esa-up <target.ipynb>
  - an alias of `esa-up`
- esa-token
  - show your token and team name

### config file
The config file (~/.esapyrc) should be written in yaml format.
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
This package is released under the MIT license (see LICENSE file).
