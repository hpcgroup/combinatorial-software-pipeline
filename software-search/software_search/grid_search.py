import itertools
from .software import Software, SoftwareRange

class GridSearch:

    def __init__(self):
        pass

    def set_software(self, software):
        self.software = software
    
    def set_compiler_search_space(self, compilers):
        self.compiler_search_space = compilers

    def set_software_search_space(self, softwares):
        self.software_search_space = softwares

    def inform(self, time):
        self.last_time = time

    def search_space(self):
        # [ [range, range, software], [range, range, range]]
        dependencies = []

        for dependency in self.software_search_space:
            softwares_flattened = []
            for s in dependency:
                if type(s) is Software:
                    softwares_flattened.append(s)
                elif type(s) is SoftwareRange:
                    softwares_flattened.extend([x for x in s.versions()])
            
            dependencies.append(softwares_flattened)

        for element in itertools.product(self.compiler_search_space, *dependencies):
            yield element