# nbformat 仕様まとめ

以下は全て Jupyterlab で検証した。検証環境は最後にまとめる。



## 気になっていたこと

- コード／アウトプットをそれぞれdetailsタグで畳みたい
- attachmentイメージがnbconvertでは出力されない
- Qutipだと出力がlatexだったり普通のテキストだったりする
- qutipでは`equation*`環境が使われているが、esa.ioで対応しているのか？
- markdownセルのdesplay数式を` ```math ... ``` `にしたい



## nbformat version 4

### Cell type

```json
{
  "cell_type" : "type",
  "metadata" : {},
  "source" : "single string or [list, of, strings]",
}
```



cell_type は次の3通り (raw, markdown, code) が存在する

- raw

  - ただの文字として扱われる

  - ```markdown: cell の例
    {
        "cell_type": "raw",
        "metadata": {},
        "source": [
    	    "This is raw code cell\n",
        	"This is raw code cell"
        ]
    },
    ```

- markdown

  - latex数式を含みうるmarkdown文字列として扱われる

  - ```markdown:cellの例
    {
        "attachments": {
            "image.png": {
                "image/png": "base64-encoded-png-data"
            }
        },
        "cell_type": "markdown",
        "metadata": {},
        "source": [
           "markdown cell with an attached image\n",
            "![image.png](attachment:image.png)"
        ]
    },
    ```

  - attachmentイメージは仕様上、ファイル名(image.png) を介して複数添付可能だが、jupyter上で複数回コピペをしてもattachements/imag.pngは1つしか生成されなかった。上書き動作をしている。

- code

  - pythonスクリプト or ipythonマジックコマンドとして扱われ、outputs（outputブロックの配列）を持つ

  - outputブロックの種類（output_type）は次の5種類 (なし, stream, execute_result, display_data, error)

    - outputブロックなし

    - stream output

      - `print()`など標準出力にアクセスする場合
      - `!dir`などシステムコマンドにアクセスした場合
      - ANSIカラーコードが入ってくる可能性がある。普通にprintしてる分には指定しない限り入ってこないが、外部コマンド呼ぶ場合はカラーコードがくるだろう。

    - execute_result

      - コード部の最後のオブジェクトを表示する場合など

        ```python: source
        a = np.arange(10)
        a
        ```

      - dataブロックに複数の形式をもつ場合がある。例えばQObjを表示させると、

        ```json
        {
            "cell_type": "code",
            "execution_count": 9,
            "metadata": {},
            "outputs": [
                {
                    "data": {
                        "text/latex": [
                            "Quantum object: dims = [[2], [2]], shape = (2, 2), type = oper, isherm = True\\begin{equation*}\\left(\\begin{array}{*{11}c}1.0 & 0.0\\\\0.0 & -1.0\\\\\\end{array}\\right)\\end{equation*}"
                        ],
                        "text/plain": [
                            "Quantum object: dims = [[2], [2]], shape = (2, 2), type = oper, isherm = True\n",
                            "Qobj data =\n",
                            "[[ 1.  0.]\n",
                            " [ 0. -1.]]"
                        ]
                    },
                    "execution_count": 9,
                    "metadata": {},
                    "output_type": "execute_result"
                }
            ],
            "source": [
                "sigmaz()"
            ]
        },
        ```

        となる。JupyterNotebook上では`text/latex`、ipython上では`text/plain`を表示する。

        - pandas.DataFrameを表示させると`text/html`と`text/plain`が入っている
        
- 仕様上、このデータとして`image/png`も入りうるようだが、matplotlibの場合は次のdisplay_dataになる。もしかしたらPILとか使う場合にくるかもしれないが、未調査。
      
- display_data
    
  - matplotlibで図を作るとこうなる
    
    - `image/png`に図のデータ、`text/plain`にalt-textが入っている
        - Figureを複数作成するとoutputsの中身が増える（ひとつのoutputブロックに図はひとつ）
    
  - どういうときに`application/json`がくるかは不明
    
  - ```json
        {
          "output_type" : "display_data",
          "data" : {
            "text/plain" : "[multiline text data]",
            "image/png": "[base64-encoded-multiline-png-data]",
            "application/json": {
              # JSON data is included as-is
              "key1": "data",
              "key2": ["some", "values"],
              "key3": {"more": "data"}
            },
            "application/vnd.exampleorg.type+json": {
              # JSON data, included as-is, when the mime-type key ends in +json
              "key1": "data",
              "key2": ["some", "values"],
              "key3": {"more": "data"}
            }
          },
          "metadata" : {
            "image/png": {
              "width": 640,
              "height": 480,
            },
          },
        }
        ```
    
- error
    
  - ```json
    {
            "cell_type": "code",
        "execution_count": 2,
            "metadata": {},
        "outputs": [
                {
                    "ename": "SyntaxError",
                    "evalue": "invalid syntax (<ipython-input-2-a5d19f64281b>, line 2)",
                    "output_type": "error",
                    "traceback": [
                        "\u001b[1;36m  File \u001b[1;32m\"<ipython-input-2-a5d19f64281b>\"\u001b[1;36m, line \u001b[1;32m2\u001b[0m\n\u001b[1;33m    for i in range(10)  # :\u001b[0m\n\u001b[1;37m                           ^\u001b[0m\n\u001b[1;31mSyntaxError\u001b[0m\u001b[1;31m:\u001b[0m invalid syntax\n"
                    ]
                }
            ],
            "source": [
                "# this code doesn't work due to including a syntax error.\n",
                "for i in range(10)  # :\n",
                "print(i)"
            ]
        },
        ```
    
      - 途中でエラーが起きた場合



### metadata

それぞれの階層で好きなデータを埋め込むことができる。Notebook, cell, outputブロックの中に`metadata`というキーでjsonデータを挿入可能。ただしバッティングを避けるため識別子として十分な一意性が必要。

以下にesapyの実装と関係ありそうなものを挙げる。詳細は後述。

- Notebook
  - 特になし
- Cell
  - collapsed
  - scrolled
  - jupyter.source_hidden
  - jupyter.outputs_hidden
- Output
  - isolated



### metadataの保存性について

- notebook
  - notebook.metadataにkey/valueを追加してからrestart & run all
    - 保存された
- cell
  - cell.metadataにkey/valueを追加してから該当セルを実行
    - 保存された
  - cell.metadataにkey/valueを追加してから該当セルを移動
    - 保存された
  - cell.metadataにkey/valueを追加してから該当セルをコピー＆ペースト
    - 保存された
  - cell.metadataにkey/valueを追加してから該当セルをカット＆ペースト
    - 保存された
- output
  - output.metadataにkey/valueを追加してから該当セルを実行
    - 上書きされた

以上より、outputブロック内以外は全て保存されることがわかった。



## esapyの実装に関するメモ

### 折りたたみ

- codeセル
  - 出力をjupyter上で折りたたんだ場合、`cell.metadata.collapsed` と `cell.metadata.jupyter.outputs_hidden` が両方trueになる。
  - 一方、ソースを折りたたんだ場合、`cell.metadata.jupyter.outputs_hidden` のみがtrueになる
- markdownセル
  - `cell.metadata.jupyter.source_hiden`で制御されている
- rawセル
  - `cell.metadata.jupyter.source_hiden`で制御されている

### スクロール

- セル出力をスクロール化にした場合、`cell.metadata.scrolled`がtrueになる
- スクロールは出力に対してon/offできるようで、markdownセルに対してenable scrollしても変化しない



# 検証環境

```shell
> conda list jupyter
# packages in environment at C:\Users\MIZUNO\Anaconda3\envs\py37:
#
# Name                    Version                   Build  Channel
jupyter                   1.0.0                    py37_7
jupyter_client            6.1.2                      py_0
jupyter_console           6.1.0                      py_0
jupyter_contrib_core      0.3.3                      py_2    conda-forge
jupyter_contrib_nbextensions 0.5.1                    py37_0    conda-forge
jupyter_core              4.6.3                    py37_0
jupyter_highlight_selected_word 0.2.0                 py37_1000    conda-forge
jupyter_latex_envs        1.4.4                 py37_1000    conda-forge
jupyter_nbextensions_configurator 0.4.1                    py37_0    conda-forge
jupyterlab                1.2.6              pyhf63ae98_0
jupyterlab-git            0.10.0                    <pip>
jupyterlab-templates      0.2.2                     <pip>
jupyterlab_code_formatter 1.1.0                      py_0    conda-forge
jupyterlab_server         1.1.0                      py_0

> conda list nb
# packages in environment at C:\Users\MIZUNO\Anaconda3\envs\py37:
#
# Name                    Version                   Build  Channel
jupyter_contrib_nbextensions 0.5.1                    py37_0    conda-forge
jupyter_nbextensions_configurator 0.4.1                    py37_0    conda-forge
nbconvert                 5.6.1                    py37_0
nbdime                    1.1.0                     <pip>
nbdime                    2.0.0            py37hc8dfbb8_0    conda-forge
nbformat                  5.0.4                      py_0
widgetsnbextension        3.5.1                    py37_0
```

