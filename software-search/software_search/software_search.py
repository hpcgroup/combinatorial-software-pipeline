'''
author: Daniel Nichols
date: August 2021
'''

def build_spec(spec_str, spack_env=None, dry=False):
    commands = []

    spack_env_str = ''
    if spack_env:
        spack_env_str = '-e {}'.format(spack_env)

    commands.append('spack {} install {}'.format(spack_env_str, spec_str))

    if dry:
        print('\n'.join(commands))
        return
    
    # run commands


def run_and_profile(software, runner, spack_env=None, dry=False):
    if spack_env:
        runner.set_spack_env(spack_env)

    if dry:
        print('\n'.join(runner.get_commands(software)))
        return
    
    runner.run(software)

def search(search_strategy, runner, main_software, compilers, dependencies, dry=False, 
    do_build=True, do_run=True, spack_env=None):

    search_strategy.set_software(main_software)
    search_strategy.set_compiler_search_space(compilers)
    search_strategy.set_software_search_space(dependencies)

    if spack_env:
        runner.set_spack_env(spack_env)

    for compiler, *software in search_strategy.search_space():
        # BUILD
        build_spec_str = main_software.get_spack_spec(compiler=compiler, dependencies=software)
        if do_build:
            build_spec(build_spec_str, spack_env=spack_env, dry=dry)

            runner.set_spack_load(build_spec_str)

        # RUN
        if do_run:
            perf_metric = run_and_profile(main_software, runner, dry=dry)

            # INFORMED NEXT GUESS
            search_strategy.inform(perf_metric)

        print('\n')
