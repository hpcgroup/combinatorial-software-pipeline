#!/usr/bin/env python3
'''
A script for intelligently launching a set of jobs over combinatorial install space.
Is dependent upon the input configurations provided by generate-input-configs.py
author: Daniel Nichols
date: July 2021
'''

# std imports
from argparse import ArgumentParser
import subprocess
import os
from math import ceil
from os.path import join as path_join, abspath
from json import dump as dump_json, dumps as dump_json_to_string, load as load_json

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
    parser.add_argument('-i', '--input', required=True, type=str, help='Experiments json file.')
    parser.add_argument('--dry', '--dry-run', action='store_true', help='Print out the commands, which would be run, \
        but do not run them.')
    parser.add_argument('--sync', action='store_true', help='Submit jobs without dependencies, so that they can/might \
        run asynchronously.')
    parser.add_argument('--collate', action='store_true', help='Submit jobs with same resources requirements as job array.')
    parser.add_argument('--ranks-per-node', type=int, default=32, help='Run with this many ranks per node.')
    parser.add_argument('--build-script', type=str, default='build-dependencies.slurm', help='The script used to build dependencies.')
    parser.add_argument('--run-script', type=str, default='run-experiment.slurm', help='The script used to run jobs.')
    parser.add_argument('--max-build-time', type=str, default='01:00:00', help='Max amount of time to spend in build script.')
    parser.add_argument('--profile', action='store_true', help='Record HPCToolkit profiles.')
    parser.add_argument('--output-root', required=True, type=str, help='Root directory to put output information into.')
    parser.add_argument('--spack-env', type=str, default='software-performance-study', help='Spack environment to use for installs.')
    parser.add_argument('--csv-file', type=str, default='data.csv', help='Name of csv file to write out data into.')
    parser.add_argument('-n', '--repeat-experiments', type=int, default=1, help='How many times to run each experiment.')
    return parser.parse_args()


def get_module_list(experiment):
    '''
    Return a list of modules to load.
    '''
    modules = [x['module'] for x in experiment.values() if isinstance(x, dict) and 'module' in x]
    return ' '.join(modules)


def get_spec_from_experiment(experiment):
    '''
    Return the spec to install.
    '''
    # collect non mpi or compiler specs
    other_specs = [x for x in experiment.values() if isinstance(x, dict) and 'name' in x and 'version' in x]
    other_specs_str = ' '.join(
        map(lambda x: '^{}'.format(get_spec(x['name'], version=x['version'])), other_specs)
    )

    spec_str = '{}%{}@{} ^{}@{} {}'.format(experiment['spec'], 
        experiment['compiler']['name'], experiment['compiler']['version'], 
        experiment['mpi']['name'], experiment['mpi']['version'],
        other_specs_str)
    return spec_str


def get_spec(name, version=None):
    '''
    Format spec according to name and version.
    '''
    if version is not None:
        return '{}@{}'.format(name, version)
    else:
        return name


def get_src_dir(spack_env, spack_spec, app_name, verbosity=0):
    '''
    Get the src directory of a spack install.
    '''
    vprint(verbosity, CHATTY, '\tRunning \'spack location ...\' to find path for spec \'{}\'.'.format(spack_spec))
    cmd_result = subprocess.run(['spack', 'location', '-i', spack_spec],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    if cmd_result.returncode != 0:
        vprint(verbosity, BASIC, '\tUnable to find src directory. Using environment location.')

        backup_result = subprocess.run(['spack', 'location', '-e', spack_env],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
        return str(backup_result.stdout)

    vprint(verbosity, CHATTY, '\tFound spec \'{}\' at \'{}\'.'.format(spack_spec, cmd_result.stdout.strip()))
    return str(path_join(cmd_result.stdout, 'share', app_name, 'src'))


def get_env(experiment, spack_env, output_root, csv_file='data.csv', profile=True, verbosity=0):
    '''
    Setup the environment variables for an experiment
    '''
    env = {}

    # SPACK_ENV_NAME - environment to use
    # SPACK_SPEC - spec to load to run application
    # PROFILE - 1 to profile with HPCTOOLKIT, 0 to not profile
    # APP_NAME - name of application to run (assumed in path)
    # APP_ARGS - input arguments to application
    # SRC_DIR - source code of application
    # MODULE_LIST - modules to load
    # OUTPUT_ROOT - root to write output info
    # EXPERIMENT_JSON - json experiment string
    # CSV_FILE - path to csv file
    
    env['SPACK_ENV_NAME'] = str(spack_env)
    env['SPACK_SPEC'] = get_spec_from_experiment(experiment)
    env['PROFILE'] = "1" if profile else "0"
    env['APP_NAME'] = experiment['app name']
    env['APP_ARGS'] = experiment['input']
    env['SRC_DIR'] = get_src_dir(spack_env, env['SPACK_SPEC'], experiment['app name'], verbosity=verbosity)
    env['MODULE_LIST'] = get_module_list(experiment)
    env['OUTPUT_ROOT'] = str(output_root)
    env['EXPERIMENT_JSON'] = dump_json_to_string(experiment).replace('"', '\\"').replace("'", "\\'")
    env['CSV_FILE'] = str(path_join(output_root, csv_file))

    return env


def get_num_nodes(ranks, ranks_per_node):
    '''
    Return the total number of nodes needed for this set of ranks.
    '''
    return int( ceil(float(ranks) / ranks_per_node) )


def build_dependencies(experiments, spack_env, build_script, build_stdout, build_stderr, max_build_time='05:00:00', 
    dry=False, verbosity=0):
    '''
    Create yaml for package and call build script.
    '''
    from yaml import dump as dump_yaml

    specs = set()
    mpis = set()
    compilers = set()

    vprint(verbosity, CHATTY, 'Collecting unique dependencies.')
    for experiment in experiments:
        specs.add(experiment['spec'])
        mpis.add(get_spec(experiment['mpi']['name'], version=experiment['mpi']['version']))
        compilers.add("%" + get_spec(experiment['compiler']['name'], version=experiment['compiler']['version']))
    
    # create yaml package
    package = {
        'spack': {
            'definitions': [
                {'packages': list(specs)},
                {'mpis': list(mpis)},
                {'compilers': list(compilers)},
                {'singleton_packages': []},
            ],
            'specs': [
                {'matrix': [
                    ['$packages'],
                    ['$^mpis'],
                    ['$compilers']  
                ]},
                '$singleton_packages'
            ]
        }
    }

    # get the output file
    vprint(verbosity, CHATTY, 'Getting spack package location.')
    config_command_result = subprocess.run(['spack', '-e', spack_env, 'config', 'edit', '--print-file'], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    if config_command_result.returncode != 0:
        print('Error getting path to spack package. Exiting.')
        exit(config_command_result.returncode)
    
    # set the package yaml file
    fpath = config_command_result.stdout.strip()
    vprint(verbosity, CHATTY, 'Writing spack package at \'{}\'.'.format(fpath))
    with open(fpath, 'w') as fp:
        dump_yaml(package, fp)

    # call build script
    BUILD_CMD = ['sbatch', '-N1', '-t', max_build_time, '-J', 'build-dependencies', '-o', build_stdout, '-e', build_stderr, build_script]
    vprint(verbosity, CHATTY, 'Running command \'{}\'.'.format(' '.join(BUILD_CMD)))

    build_jobid = -1
    if not dry:
        build_command_result = subprocess.run(
                BUILD_CMD,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=dict(os.environ, SPACK_ENV_NAME=spack_env),
                universal_newlines=True
            )
        
        build_jobid = build_command_result.stdout.split()[-1]
        vprint(verbosity, BASIC, 'Submitted build job with id \'{}\'.'.format(build_jobid))

    return build_jobid
    


def run_experiments(experiments, build_script, run_script, root, spack_env, num_repeats=1, csv_file='data.csv', 
    profile=True, ranks_per_node=32, max_build_time='04:00:00', sync=True, dry=False, verbosity=0):
    '''
    Submits jobs to SLURM job scheduler.
    '''

    SUBMIT_CMD = 'sbatch'

    root = abspath(root)
    build_stdout, build_stderr = path_join(root, 'build-%A.stdout'), path_join(root, 'build-%A.stderr')
    run_stdout, run_stderr = path_join(root, 'run-%A.stdout'), path_join(root, 'run-%A.stderr')
    
    # build script
    build_jobid = build_dependencies(experiments, spack_env, build_script, build_stdout, build_stderr, 
        max_build_time=max_build_time, verbosity=verbosity)

    # write out the csv header
    with open(path_join(root, csv_file), 'w') as fp:
        fp.write('application,job_id,ranks,input,start_time,duration,input_config,hpctoolkit_path\n')
    
    vprint(verbosity, BASIC, 'Submitting {} jobs.'.format(len(experiments)*num_repeats))
    last_jobid = build_jobid
    for experiment in experiments:

        # setup the environment
        vprint(verbosity, CHATTY, '\tSetting up environment.')
        exp_env = get_env(experiment, spack_env, root, csv_file=csv_file, profile=profile, verbosity=verbosity)
        env = dict(os.environ)
        env.update(exp_env)

        # submit run job
        run_command = [SUBMIT_CMD, '-J', 'run-experiment', 
            '-o', run_stdout, '-e', run_stderr,
            '-N', str(get_num_nodes(experiment['ranks'], ranks_per_node)),
            '-n', str(experiment['ranks']),
            '--ntasks-per-node', str(ranks_per_node),
            '-t', str(experiment['max wall time']),
            '--dependency', 'afterok:{},afterany:{}'.format(build_jobid, last_jobid)
            ]
        
        run_command.append(run_script)
        vprint(verbosity, CHATTY, '\tRunning job \'{}\' {} times.'.format(' '.join(run_command).strip(), num_repeats))

        if not dry:
            for _ in range(num_repeats):
                # run the job
                run_command_result = subprocess.run(run_command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                # so next job depends on this one
                if sync:
                    last_jobid = run_command_result.stdout.split()[-1]



def main():
    args = get_args()

    # load input experiments
    vprint(args.verbose, BASIC, 'Loading input experiments.')
    experiments = []
    with open(args.input, 'r') as fp:
        experiments = load_json(fp)
    
    # TODO -- find similar resource jobs for collation

    # run jobs
    run_experiments(experiments, args.build_script, args.run_script, args.output_root, args.spack_env, num_repeats=args.repeat_experiments,
        csv_file=args.csv_file, profile=args.profile, ranks_per_node=args.ranks_per_node, max_build_time=args.max_build_time, 
        sync=args.sync, dry=args.dry, verbosity=args.verbose)
    


if __name__ == '__main__':
    main()