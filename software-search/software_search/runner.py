import time
import subprocess
from .utilities import listify

class BashRunner():
    
    def __init__(self):
        self.use_mpi = False
        self.spack_env = None
        self.spack_loads = []
    
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

    def get_commands(self, software):
        commands = []

        spack_env_str = ''
        if self.spack_env:
            commands.extend([
                'spack env deactivate',
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

    def run(self, software):
        commands = self.get_commands(software)

        # run commands
        for cmd in commands[:-1]:
            res = subprocess.run(cmd.split(' '))
            if res.returncode != 0:
                return
        
        start = time.time()
        res = subprocess.run(commands[-1].split(' '))
        duration = time.time() - start

        