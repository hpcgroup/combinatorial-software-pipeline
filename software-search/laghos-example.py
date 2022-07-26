from argparse import ArgumentParser
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
    return parser.parse_args()


def main():
    args = get_args()

    mpis = [
        Software('openmpi').make_range(versions=['4.0.5', '3.1.6']),
        Software('mvapich2').make_range(versions=['2.3.4', '2.2'])
    ]

    mfem = [
        Software('mfem').make_range(versions=['4.2.0', '4.1.0'], variants=['libceed', 'lapack', 'metis'])
    ]

    compilers = [
        Compiler('gcc', version='8.3.1')
    ]

    main_software = Software('laghos', version='3.1', run_cmd='laghos',
                            variants='', run_args='-p 1 -dim 3 -rs 2 -tf 0.6 -pa')

    search_strategy = GridSearch()
    #search_strategy = RandomSearch(max_iter=2)
    runner = BashRunner()
    runner.set_mpi(num_ranks=4)

    search(search_strategy, runner, main_software, compilers, 
        [mfem, mpis], dry=args.dry, spack_env=args.spack_env)
    


if __name__ == '__main__':
    main()