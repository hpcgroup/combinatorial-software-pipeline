import copy
import itertools
from spack.spec import Spec
from spack.cmd.install import install_specs
from spack.build_environment import setup_package
from .compiler import Compiler
from .utilities import *

class SoftwareRange:
    def __init__(self, software, versions=[], variants=[]):
        self.software_ = software
        self.versions_ = versions
        self.variants_ = variants
    
    def versions(self):
        if len(self.variants_) == 0:
            for version in self.versions_:
                software_copy = copy.deepcopy(self.software_)
                software_copy.version = version
                yield software_copy
        else:
            for version, variant_mask in itertools.product(self.versions_, range(2 ** len(self.variants_))):
                software_copy = copy.deepcopy(self.software_)
                software_copy.version = version
                software_copy.variants = [('+' if variant_mask & (1<<n) else '~') + v for n,v in enumerate(self.variants_)]
                yield software_copy


class Software:
    '''
    A wrapper for spack specs and run information.
    '''

    def __init__(self, name, spec_name=None, version=None, variants='',
        run_cmd=None, run_args=''):
        self.name = name

        self.spec_name = spec_name if spec_name else name
        if version:
            self.version = version
        self.variants = variants

        self.run_cmd = run_cmd if run_cmd else name
        self.run_args = run_args
        self.spec_hash = None

    
    def get_spack_spec(self, compiler=None, dependencies=None):
        ''' Returns the spack spec for this Software object. Includes
            version, compiler, variants, and dependencies.
        '''
        base_str = ''
        if hasattr(self, 'version'):
            base_str = '{}@{}'.format(self.name, self.version)
        else:
            base_str = '{}'.format(self.name)

        variants_str = ''
        if isinstance(self.variants, list):
            variants_str = ' '.join(self.variants)
        else:
            variants_str = self.variants
        
        if compiler is None:
            full_spec_str = '{} {}'.format(base_str, variants_str)
        else:
            full_spec_str = '{}%{} {}'.format(
                                            base_str, 
                                            compiler.get_compiler_spec(),
                                            variants_str
                                        )

        if dependencies:
            dependencies = listify(dependencies)
            dependencies_list = map(
                                    lambda x: '^{}'.format(x.get_spack_spec()),
                                    dependencies
                                )
            dependencies_str = ' '.join(dependencies_list)
            full_spec_str = '{} {}'.format(full_spec_str, dependencies_str)

        return full_spec_str

    def __str__(self):
        return self.get_spack_spec()

    def __repr__(self):
        return self.get_spack_spec()

    def get_run_command(self):
        cmd_str = '{} {}'.format(self.run_cmd, self.run_args)
        return cmd_str

    def get_run_command_api(self):
        run_cmd = self.concrete_spec.prefix.bin.join(self.run_cmd)
        cmd_str = '{} {}'.format(run_cmd, self.run_args)
        return cmd_str

    def get_mpi_command_api(self, mpi_cmd):
        return self.concrete_spec['mpi'].prefix.bin.join(mpi_cmd)
    
    def make_range(self, versions=[], variants=[]):
        return SoftwareRange(self, versions=versions, variants=variants)

    def set_abstract_spec(self, compiler, dependencies):
        spec_str = self.get_spack_spec(compiler=compiler, dependencies=dependencies)
        self.abstract_spec = Spec(spec_str)

    def concretize(self):
        self.concrete_spec = self.abstract_spec.concretized()
        self.hash = self.concrete_spec.dag_hash()

    def install():
        package = self.concrete_spec.package
        package.do_install()

    def get_path_to_binary(self):
        return self.concrete_spec.prefix.bin.join(self.run_cmd)

    def get_path_to_mpi_binary(self, mpi_cmd):
        return self.concrete_spec['mpi'].prefix.bin.join(mpi_cmd)

    def setup_software(self, dirty=False, context='test'):
        setup_package(self.concrete_spec.package, dirty=dirty, context=context)

    def setup_mpi(self, dirty=False, context='test'):
        setup_package(self.concrete_spec['mpi'].package, dirty=dirty, context=context)

