'''
author: Daniel Nichols
date: August 2021
'''

def build(software, compiler, dependencies, runner, spack_env=None, dry=False):

    if spack_env:
        runner.set_spack_env(spack_env)

    if dry:
        print('\n'.join(runner.get_build_commands(software, compiler, dependencies)))
        return
    
    # run commands
    runner.build(software, compiler, dependencies)


def run_and_profile(software, compiler, dependencies, runner, spack_env=None, dry=False):
    if spack_env:
        runner.set_spack_env(spack_env)

    if dry:
        print('\n'.join(runner.get_commands(software, compiler, dependencies)))
        return
    
    runner.run(software, compiler, dependencies)


def search(search_strategy, runner, main_software, compilers, dependencies, dry=False, 
    do_build=True, do_run=True, spack_env=None):

    search_strategy.set_software(main_software)
    search_strategy.set_compiler_search_space(compilers)
    search_strategy.set_software_search_space(dependencies)

    if spack_env:
        runner.set_spack_env(spack_env)

    for compiler, *software in search_strategy.search_space():
        # BUILD
        if do_build:
            build(main_software, compiler, software, runner, spack_env=spack_env, dry=dry)

        # RUN
        if do_run:
            perf_metric = run_and_profile(main_software, compiler, software, runner, spack_env=spack_env, dry=dry)

            # INFORMED NEXT GUESS
            search_strategy.inform(perf_metric)

        print('\n')
