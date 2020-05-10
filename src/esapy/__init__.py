__version__ = '1.2.0'

from IPython.core.magic import register_line_cell_magic


@register_line_cell_magic
def esapy_fold(line, cell=None):
    '''This magic is just a marker.
    '''
    if cell is None:
        return line
    else:
        return line, cell


def load_ipython_extension(ipython):
    ipython.register_magics(esapy_fold)
