#!/usr/bin/env python3

'''
Analyze data from runs over combinatorial builds. Script is designed to work
with data generated from the `run-experiment.py` and `run-experiment.slurm` scripts.
author: Daniel Nichols
date: July 2021
'''

# std imports
from argparse import ArgumentParser
from os.path import join as path_join
from json import loads as load_json_from_string

# 3rd party imports
import numpy as np
import pandas as pd
import hatchet as ht
import matplotlib.pyplot as plt

# local imports
from utilities import vprint, get_total_runtime

# verbosity levels
QUIET = 0
BASIC = 1
CHATTY = 2


def get_args():
    '''
    Generate the set of cl args passed to this run instance.
    '''
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', nargs='?', default=0, const=1, type=int, help='Verbosity. 1 for just important \
        output, 2 for full output. No args defaults to 1.')
    parser.add_argument('-i', '--input', type=str, required=True, help='Path to input CSV data file.')
    parser.add_argument('-p', '--plot', type=str, nargs='?', const='.', help='Plot figures. Optional value to plot figures in the \
        provided directory.')
    parser.add_argument('--no-hpctoolkit', action='store_true', dest='skip_hpctoolkit', help='Do not read HPCToolkit \
        profiles if provided.')
    return parser.parse_args()


def read_hpctoolkit_profile(fpath, safe=True):
    '''
    Uses Hatchet to read HPCToolkit profile. If 'safe', then wrap in try/except and 
    return None on error.
    '''
    if safe:
        gf = None
        try:
            gf = ht.GraphFrame.from_hpctoolkit(fpath)
        except:
            gf = None
        return gf
    else:
        return ht.GraphFrame.from_hpctoolkit(fpath)


def parse_config_json(json_string, safe=True):
    '''
    Parse a json object into string. If 'safe', then wrap the call in try/except
    and return None on error.
    '''
    if safe:
        obj = None
        try:
            obj = load_json_from_string(json_string)
        except:
            obj = None
        return obj
    else:
        return load_json_from_string(json_string)


def read_data(fpath, skip_hpctoolkit=False, verbosity=0):
    '''
    Read the input data in fpath. Return 
    '''
    vprint(verbosity, BASIC, 'Reading CSV data file at \'{}\'.'.format(fpath.strip()))
    df = None
    with open(fpath, 'r') as fp:
        df = pd.read_csv(fp, quotechar='"', escapechar='\\')

        if not skip_hpctoolkit:
            # read in the hpctoolkit profiles
            vprint(verbosity, BASIC, 'Reading HPCToolkit profiles.')

            gf_objects = df['hpctoolkit_path'].apply(lambda row: read_hpctoolkit_profile(row))
            gf_objects = gf_objects.rename('hpctoolkit_profile')
            df = pd.concat([df, gf_objects], axis='columns')
    
    return df
            

def parse_data(df, skip_hpctoolkit=False, aggregate=True, verbosity=0):
    '''
    Parse data within the profiles.
    '''
    vprint(verbosity, BASIC, 'Parsing and preprocessing data in dataframe.')

    # first parse json strings into objects
    vprint(verbosity, CHATTY, 'Parsing JSON config column.')
    config_objects = df['input_config'].apply(lambda row: parse_config_json(row))
    config_objects = config_objects.rename('input_config_object')
    df = pd.concat([df, config_objects], axis='columns')

    # add mpi and compiler columns
    vprint(verbosity, CHATTY, 'Adding MPI and compiler columns from input data.')
    mpi_objects = df['input_config_object'].apply(lambda row: '{}@{}'.format(row['mpi']['name'], row['mpi']['version']))
    compiler_objects = df['input_config_object'].apply(lambda row: '{}@{}'.format(row['compiler']['name'], row['compiler']['version']))
    mpi_objects = mpi_objects.rename('mpi')
    compiler_objects = compiler_objects.rename('compiler')
    df = pd.concat([df, mpi_objects, compiler_objects], axis='columns')

    # default to runtime reported by bash timing
    run_time_column = 'duration'

    # get total runtime from HPCToolkit profiles
    if not skip_hpctoolkit:
        vprint(verbosity, CHATTY, 'Calculating run time stats from Hatchet GraphFrames.')

        run_time_column = 'main_run_time'
        df[run_time_column] = df['hpctoolkit_profile'].apply(get_total_runtime)
        

    # aggregate same runs
    vprint(verbosity, CHATTY, 'Find mean stats across multiple runs of same experiment.')
    min_duration = df[run_time_column].min()
    error_func = lambda x: x.astype(float).std() / np.sqrt(x.astype(float).count())
    min_mult_min_duration_func = lambda x: x.astype(float).min() / min_duration
    mean_mult_min_duration_func = lambda x: x.astype(float).mean() / min_duration
    grouped_df = df.groupby(by=['application', 'ranks', 'input', 'compiler', 'mpi'])
    runtimes_df = grouped_df.agg({run_time_column: ['mean', 'min', 'max', 'median', 'std', 'count',
        error_func, min_mult_min_duration_func, mean_mult_min_duration_func]})
    runtimes_df.rename(columns={'<lambda_0>': 'error', '<lambda_1>': 'min_mult_min', '<lambda_2>': 'mean_mult_min'}, inplace=True, level=1)

    return df, runtimes_df


def compare_two_softwares(softwares, agg_df, compare_by='mean', plot=False, verbosity=0):
    '''
    Compare two softwares across runtimes.
    '''
    assert len(softwares) == 2

    vprint(verbosity, BASIC, 'Comparing {} and {}.'.format(softwares[0], softwares[1]))
    vprint(verbosity, BASIC, str(agg_df))


    if plot:
        minimal_df = agg_df.reset_index()
        pivot_df = minimal_df.pivot(index='compiler', columns='mpi', values=('main_run_time', 'mean'))
        error_df = minimal_df.pivot(index='compiler', columns='mpi', values=('main_run_time', 'error'))
        app_name = minimal_df['application'].iloc[0]
        num_ranks = minimal_df['ranks'].iloc[0]
        
        # TODO -- weird edge case for Quartz default softwares
        pivot_df['openmpi@4.1.0'] = pivot_df['openmpi@4.1.0'].fillna(pivot_df['openmpi@4.0.0'])
        error_df['openmpi@4.1.0'] = error_df['openmpi@4.1.0'].fillna(error_df['openmpi@4.0.0'])
        pivot_df.drop(columns='openmpi@4.0.0', inplace=True)
        error_df.drop(columns='openmpi@4.0.0', inplace=True)
        #pivot_df = pivot_df * 60.0
        #error_df = error_df * 60.0 # TODO -- I don't think this is mathematically correct.

        # use pandas to make group plot
        ax = pivot_df.plot.bar(title='Default Compiler and MPI Versions\n{} on Quartz {} Cores'.format(app_name, num_ranks), 
            xlabel='Compiler', ylabel='Mean Run Time (sec)', rot=0, yerr=error_df)

        fname = 'compare_{}_{}-{}.pdf'.format(app_name, softwares[0], softwares[1])
        ax.get_figure().savefig(path_join(plot, fname))
        




def main():
    args = get_args()

    # read in CSV files and HPCToolkit profiles
    data_df = read_data(args.input, skip_hpctoolkit=args.skip_hpctoolkit, verbosity=args.verbose)

    # Do some preprocessing on the data.
    data_df, agg_df = parse_data(data_df, skip_hpctoolkit=args.skip_hpctoolkit, verbosity=args.verbose)

    # compare across compiler and MPIs
    compare_two_softwares(('mpi', 'compiler'), agg_df, plot=args.plot, verbosity=args.verbose)


if __name__ == '__main__':
    main()
