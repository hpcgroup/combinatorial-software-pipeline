'''
Python utilities.
author: Daniel Nichols
date: July 2021
'''
# std imports
import numpy as np

def vprint(verbosity, log_level, message, **kwargs):
    '''
    Verbose print shorthand utility. Only print if `verbosity >= log_level`.
    '''
    if verbosity >= log_level:
        print(message, **kwargs)


def get_total_runtime(gf):
    gf = gf.deepcopy()
    gf.drop_index_levels()
    function_agg = gf.dataframe.groupby('name').sum()
    return function_agg[function_agg.index.str.startswith('main')].iloc[0]['time (inc)']