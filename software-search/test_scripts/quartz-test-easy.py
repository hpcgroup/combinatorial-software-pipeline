#!/usr/bin/env spack-python
from argparse import ArgumentParser
import os, sys
sys.path.append('..')
from software_search.software import Software
from software_search.software_search import search
from software_search.grid_search import GridSearch
from software_search.random_search import RandomSearch
from software_search.compiler import Compiler
from software_search.runner import BashRunner


def get_args():
    parser = ArgumentParser()
    parser.add_argument('-d', '--dry', action='store_true', help='Dry run.')
    parser.add_argument('-e', '--spack-env', type=str, help='Spack environment to install in.')
    parser.add_argument('-o', '--output-dir', type=str, help='Directory to log output files into')
    return parser.parse_args()


def main():
    args = get_args()

    mpis = [
        Software('openmpi', version='4.1.0'),
        Software('impi', version='2017.0')
    ]

    compilers = [
	Compiler('gcc', version='4.9.3'),
    ]

    main_software = Software('laghos', version='3.1', run_cmd='laghos',
                            variants='', run_args='-p 1 -dim 2 -rs 4 -tf 0.6 -pa')

    search_strategy = GridSearch()
    #search_strategy = RandomSearch(max_iter=2)
    runner = BashRunner(output_dir='/usr/workspace/synk1/combinatorial-software-pipeline/software-search/quartz-test-outputdir')
    runner.set_mpi(num_ranks=32)

    search(search_strategy, runner, main_software, compilers, 
        [mpis], dry=args.dry, spack_env=args.spack_env)


if __name__ == '__main__':
    main()
