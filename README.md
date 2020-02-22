# esapy

A python implementation of esa.io API

The main purpose of this package is implementation of easy uploading and sharing jupyter notebook to esa.io service.



## INSTALATION

1. Install pandoc

    ```shell
    sudo apt install pandoc
    ```
    
    This package call nbconvert internally.

1. Install package

    ```shell
    pip install esapy
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
    esa-up target.ipynb
    ```

    This package (for now) will call nbconvert and upload images, and will not upload markdown file as new post.

1. Post a new article by copy-and-paste the generated markdown file.







## License
Copyright (c) 2020 Kosuke Mizuno  
This package is released under the MIT license (see LICENSE file).
