#!/usr/bin/env spack-python
from argparse import ArgumentParser
import json
import matplotlib.pyplot as plt
import numpy as np
import spack


def get_args():
    # TODO MAKE THIS WORK WITH A VARIABLE NUMBER OF JSON FILES
    parser = ArgumentParser()
    parser.add_argument('-o', '--input-one', type=str, help='json file containing data')
    parser.add_argument('-t', '--input-two', type=str, help='json file containing data')
    return parser.parse_args()

def get_json(fname1, fname2):
    json1 = {}
    json2 = {}

    with open(fname1) as fp:
        json1 = json.load(fp)

    with open(fname2) as fp:
        json2 = json.load(fp)

    return json1, json2

#TODO BETTER VARIABLE NAMES
def get_average(run1, run2):
    avg_list = [] 
    n = len(run1)
    m = len(run2)
    assert(n == m)

    # Sort lexically by hash

    for i in range(n):
        build1 = run1[i]
        build2 = run2[i]
        assert(build1['hash'] == build2['hash'])

        avg_build = {}
        avg_build['hash'] = build1['hash']
        avg_build['ymd'] = None
        if (build1['figure_of_merit'] == None) or (build2['figure_of_merit'] == None):
            avg_build['figure_of_merit'] = None
        else:
            avg_build['figure_of_merit'] = (build1['figure_of_merit'] + build2['figure_of_merit']) / 2

        avg_list.append(avg_build)

    return avg_list

def generate_abstract_specs(build_list):
    abstract_spec_list = []
    for build in build_list:
        spc = spack.spec.Spec('/{}'.format(build['hash']))
        print(spc)
        abstract_spec = 'compiler = {}, mpi = {}'.format(spc.compiler, spc['mpi'])
        abstract_spec_list.append(abstract_spec)

    return abstract_spec_list

#TODO BETTER VARIABLE NAMES
def generate_plot(build_list):
    plt.rcdefaults()
    fig, ax = plt.subplots()
    y_pos = np.arange(len(build_list))


#TODO MAKE OUTPUT JSON DATA BE SORTED BY HASH
def main():
    args = get_args()
    run1, run2 = get_json(args.input_one, args.input_two)
    run1 = sorted(run1, key=lambda build: build['hash'])
    run2 = sorted(run2, key=lambda build: build['hash'])
    avg = get_average(run1, run2)
    abstract_spec_list = generate_abstract_specs(avg)

    print(run1)
    print('\n')
    print(run2)
    print('\n')
    print(avg)
    print('\n')
    print(abstract_spec_list)

if __name__ == "__main__":
    main()
