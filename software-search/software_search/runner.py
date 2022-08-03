from hashlib import md5
import time
import subprocess
import argparse
from spack.spec import Spec
from spack.cmd.install import install_specs
from .utilities import listify

class BashRunner():
    
    def __init__(self, output_dir=None):
        self.use_mpi = False
        self.spack_env = None
        self.spack_loads = []
        self.output_dir = output_dir
    
    def set_spack_env(self, spack_env):
        self.spack_env = spack_env

    def set_spack_load(self, specs):
        if type(specs) == str:
            self.spack_loads = [specs,]
        else:
            self.spack_loads = listify(specs)

    def set_mpi(self, num_ranks, run_cmd='mpirun'):
        self.use_mpi = True
        self.num_ranks = num_ranks
        self.mpi_cmd = run_cmd


    def get_build_commands(self, software, compiler, dependencies):
        spack_env_str = ''
        if self.spack_env:
            spack_env_str = '-e {} '.format(self.spack_env)

        spec_str = software.get_spack_spec(compiler=compiler, dependencies=dependencies)
        build_commands_str = 'spack {}install --reuse {}'.format(spack_env_str, spec_str)

        if self.output_dir:
            spec_hash_str = str(md5(spec_str.encode()).hexdigest())
            output_file_str = '{}/{}-build.stdout'.format(self.output_dir, spec_hash_str)
            build_commands_str = '{} > {}'.format(build_commands_str, output_file_str)

        self.set_spack_load(spec_str)

        return [build_commands_str]
    
    def build(self, software, compiler, dependencies):
        commands = self.get_build_commands(software, compiler, dependencies)
        spec_str = software.get_spack_spec(compiler=compiler, dependencies=dependencies)
        self.set_spack_load(spec_str)
        
        # run commands
        for cmd in commands:
            res = subprocess.run(cmd, shell=True)
            if res.returncode != 0:
                return

        res = subprocess.run('spack find -p {}'.format(spec_str), shell=True)


    def build_using_api(self, software, compiler, dependencies):
        print("Generating abstract spec")
        software.set_abstract_spec(compiler=compiler, dependencies=dependencies)
        print("Concretizing spec: {}".format(software.abstract_spec))
        software.concretize()
        print("Installing spec: {}".format(software.concrete_spec))
        software.install(cli_args=argparse.Namespace(), kwargs={})

    def get_path_to_spec_binary(self, software, compiler, dependencies):
        print("finding command string")
        find_command_str = 'spack find -p /{}'.format(software.spec_hash)
        find_command_stdout = subprocess.run(find_command_str, shell=True, capture_output=True, text=True)
        path = find_command_stdout.stdout.splitlines()[-1].split()[-1] # This is sketchy
        return path

    def get_commands_using_api(self, software, compiler, dependencies):
        commands = []

        command_str = software.get_run_command()
        if self.use_mpi:
            command_str = '{} -n {} {}'.format(self.mpi_cmd, self.num_ranks, command_str)

        if self.output_dir:
            current_date_time = time.strftime("%Y%m%d-%H%M%S")
            output_file_str = '{}/{}-run-{}.stdout'.format(self.output_dir, software.hash, current_date_time)
            command_str = '{} > {}'.format(command_str, output_file_str)

        commands.append(command_str)
        return commands

    def get_commands(self, software, compiler, dependencies):
        commands = []

        spack_env_str = ''
        if self.spack_env:
            #commands.extend([
            #    'spack env deactivate',
            #    'spack env activate {}'.format(self.spack_env)
            #])
            commands.extend([
                'spack env activate {}'.format(self.spack_env)
            ])
            spack_env_str = '-e {}'.format(self.spack_env)

        for spec in self.spack_loads:
            load_commands_str = map(
                    lambda x: 'spack {} load {}'.format(spack_env_str, x),
                    self.spack_loads
                )
            commands.extend(load_commands_str)

        command_str = software.get_run_command()
        if self.use_mpi:
            command_str = '{} -np {} {}'.format(self.mpi_cmd, self.num_ranks, command_str)

        commands.append(command_str)
        return commands
        

    def run(self, software, compiler, dependencies):
        #commands = self.get_commands(software, compiler, dependencies)
        commands = self.get_commands_using_api(software, compiler, dependencies)
        #commands = self.get_commands(software, compiler, dependencies)
        software.setup_software()
        #software.setup_mpi()

        # run commands
        for cmd in commands[:-1]:
            print('running cmd = {}'.format(cmd))
            res = subprocess.run(cmd, shell=True)
            if res.returncode != 0:
                return
        
        print('running cmd = {}'.format(commands[-1]))
        start = time.time()
        res = subprocess.run(commands[-1], shell=True)
        duration = time.time() - start
