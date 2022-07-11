from argparse import ArgumentParser
from software_search.software import Software
from software_search.software_search import search
from software_search.grid_search import GridSearch
from software_search.compiler import Compiler
from software_search.runner import BashRunner


def get_args():
    parser = ArgumentParser()
    parser.add_argument('--dry', action='store_true', help='Dry run.')
    parser.add_argument('--spack-env', type=str, help='Spack environment to install in.')
    return parser.parse_args()


def main():
    args = get_args()

    mpis = [
        Software('openmpi').make_range(['4.0.5', '3.1.6']),
        Software('mvapich2').make_range(['2.3.4', '2.2'])
    ]

    metis = [
        Software('metis').make_range(['4.0.3', '5.1.0'])
    ]

    mfem = [
        Software('mfem', variants='+lapack').make_range(['4.2.0', '4.1.0'])
    ]

    blas = [
        Software('intel-mkl').make_range(['2020.3.279', '2020.2.254']),
        Software('openblas').make_range(['0.3.12', '0.3.11, 0.2.20']),
        Software('atlas').make_range(['3.11.41', '3.10.3'])
    ]

    compilers = [
        Compiler('gcc', version='8.3.1'),
        Compiler('intel')
    ]

    main_software = Software('laghos', version='3.1', run_cmd='laghos',
                            variants='+metis', run_args='')

    search_strategy = GridSearch()
    runner = BashRunner()
    runner.set_mpi(num_ranks=4)

    search(search_strategy, runner, main_software, compilers, 
        [mfem, blas, metis, mpis], dry=args.dry, spack_env=args.spack_env)
    


if __name__ == '__main__':
    main()