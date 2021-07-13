#!/usr/bin/env python3

'''
Generates a range of json input configurations for running the rest 
of the scripts in this repo.
author: Daniel Nichols
date: July 2021
'''

# std imports
from argparse import ArgumentParser
from sys import stdout
from json import dump as dump_json, load as load_json
from itertools import product

# local imports
from utilities import vprint

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
    parser.add_argument('-o', '--output', default='-', type=str, help='Where to output json data. If - is given, \
        then the script outputs to stdout.')
    parser.add_argument('-i', '--input', required=True, type=str, help='List of softwares to enumerate in json file.')
    parser.add_argument('-j', '--join', type=str, help='Join with an existing list of json executables.')
    parser.add_argument('-r', '--ranks', nargs='*', default=[64], help='Number of ranks to run each experiment.')
    parser.add_argument('--input-problems', nargs='*', default=[''], help='Commmand line args to run application.')
    parser.add_argument('-a', '--app', type=str, required=True, help='Spack spec of application to run.')
    parser.add_argument('--app-name', type=str, help='Shorthand name for application if different than basename in -a.')
    parser.add_argument('--max-wall-time', type=str, default='00:15:00', help='Define the max wall time to pass to SLURM \
        when running each application.')
    return parser.parse_args()


def read_json(fpath, wrap_list=False, verbosity=0):
    '''
    Load an existing set of json configs. If only a single json object, then wrap it
    in a list object. 
    '''
    vprint(verbosity, BASIC, 'Loading json at \'{}\'.'.format(fpath))

    with open(fpath, 'r') as fp:
        json_obj = load_json(fp)

    if wrap_list and isinstance(json_obj, dict):
        vprint(verbosity, CHATTY, 'Wrapping json as list.')
        json_obj = [json_obj]

    return json_obj


def get_app_name(app, app_name, verbosity=0):
    '''
    Derive shorthand from spec `app` if app_name is None.
    '''
    vprint(verbosity, CHATTY, 'Finding short app name.')
    if app_name is not None:
        return app_name
    
    from re import split as regex_split
    return regex_split('[%@\W]', app)[0]


def check_where_clauses(experiment, clauses, verbosity=0):
    '''
    Checks a 'where' exception.
    '''
    all_true = True
    for clause in clauses:
        if clause not in [x['module'] for x in experiment.values() if isinstance(x, dict) and 'module' in x]:
            all_true = False

    return all_true


def does_exception_apply(experiment, exception, verbosity=0):
    '''
    Check if this exception applies to the current experiment.
    '''
    for key, val in exception.items():
        if key == 'where' and check_where_clauses(experiment, val['pattern'], verbosity=verbosity):
                vprint(verbosity, CHATTY, 'Caught valid exception. Doing substitution.')
                return True
    
    return False


def _do_substitution(experiment, sub, verbosity=0):
    '''
    Replace matching module with this one.
    '''
    for key, val in sub.items():
        if key in experiment:
            vprint(verbosity, CHATTY, 'Replacing {} with {} in experiment.'.format(str(experiment[key]), str(val)))
            experiment[key] = val


def do_exception_replacement(experiment, exception, verbosity=0):
    '''
    Assumes exception is valid and replacement should be done.
    '''
    for key, val in exception.items():
        if 'substitution' in val:
            if len(val['substitution']) == 0:
                return False
                
            for sub in val['substitution']:
                _do_substitution(experiment, sub, verbosity=verbosity)
    
    return True


def handle_exception(experiment, software_exceptions, verbosity=0):
    '''
    Handle possible exceptions. Returns True on success, False if nothing 
    can be done.
    '''
    if software_exceptions is None:
        return True
    
    success_flag = True
    for exception in software_exceptions:
        if does_exception_apply(experiment, exception, verbosity=verbosity):
            success_flag = do_exception_replacement(experiment, exception, verbosity=verbosity)
    
    return success_flag


def clean_input_args(input_args, verbosity=0):
    '''
    Clean up the inputs provided to the script
    '''
    input_args = input_args.strip('"\'')
    return input_args


def generate_experiments(software_definitions, software_exceptions, inputs, ranks, app, app_name, max_wall_time, verbosity=0):
    '''
    Main script for generating experiments.
    Enumerates values in each set of software (keys in software definitions).
    '''

    # maintain all generated experiments
    experiments_list = []

    for i in range(len(inputs)):
        inputs[i] = clean_input_args(inputs[i], verbosity=verbosity)

    # generate tuples of all software combinations
    vprint(verbosity, BASIC, 'Generating enumerated space of software.')
    software_keys = list(software_definitions.keys())
    software_list = [software_definitions[key] for key in software_keys]
    software_keys.extend(['input', 'ranks'])
    vprint(verbosity, CHATTY, 'Enumerating ({}).'.format(', '.join(software_keys)))
    cartesian_product = product(*software_list, inputs, ranks)
    
    # build experiment object
    vprint(verbosity, BASIC, 'Building experiments table.')
    for sample in cartesian_product:
        experiment = {}
        
        # first add each column of the enumerated sample
        for key, value in zip(software_keys, sample):
            experiment[key] = value

        # meta info
        experiment['spec'] = app
        experiment['app name'] = app_name
        experiment['max wall time'] = max_wall_time

        if handle_exception(experiment, software_exceptions, verbosity=verbosity):
            experiments_list.append(experiment)
        else:
            vprint(verbosity, CHATTY, 'Skipping experiment.')

    vprint(verbosity, BASIC, 'Created {} total experiments.'.format(len(experiments_list)))

    return experiments_list


def main():
    # parse initial arguments
    args = get_args()

    # to build the enuration of parameters
    experiments = []

    # join with previous parameters
    if args.join:
        experiments = read_json(args.join, wrap_list=True, verbosity=args.verbose)

    # read input json
    software_definitions = read_json(args.input, verbosity=args.verbose)
    software_exceptions = None
    if 'exceptions' in software_definitions:
        software_exceptions = software_definitions.pop('exceptions')

    # generate experiments
    app_name = get_app_name(args.app, args.app_name, verbosity=args.verbose)
    new_experiments = generate_experiments(software_definitions, software_exceptions, args.input_problems, args.ranks, 
        args.app, app_name, args.max_wall_time, verbosity=args.verbose)
    experiments.extend(new_experiments)

    # write out final experiment
    vprint(args.verbose, BASIC, 'Writing out final experiments to \'{}\'.'.format('stdout' if args.output == '-' else args.output))
    if args.output == '-':
        dump_json(experiments, stdout)
        print() # json.dump doesn't append newline
    else:
        with open(args.output, 'w') as fp:
            dump_json(experiments, fp)


if __name__ == '__main__':
    main()
