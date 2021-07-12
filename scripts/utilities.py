'''
Python utilities.
author: Daniel Nichols
date: July 2021
'''





def vprint(verbosity, log_level, message, **kwargs):
    '''
    Verbose print shorthand utility. Only print if `verbosity >= log_level`.
    '''
    if verbosity >= log_level:
        print(message, **kwargs)