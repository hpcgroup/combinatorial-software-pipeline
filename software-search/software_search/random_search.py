import itertools
import random
from .software import Software, SoftwareRange

class RandomSearch:

    def __init__(self, max_iter=10):
        self.max_iter_ = max_iter

    def set_software(self, software):
        self.software = software
    
    def set_compiler_search_space(self, compilers):
        self.compiler_search_space = compilers

    def set_software_search_space(self, softwares):
        self.software_search_space = softwares

    def inform(self, time):
        self.last_time = time

    def search_space(self):
        dependencies = []

        for dependency in self.software_search_space:
            softwares_flattened = []
            for s in dependency:
                if type(s) is Software:
                    softwares_flattened.append(s)
                elif type(s) is SoftwareRange:
                    softwares_flattened.extend([x for x in s.versions()])
            
            dependencies.append(softwares_flattened)

        # TODO: replace this entire bit with generator, so whole list is not generated in memory
        total_space = list(itertools.product(self.compiler_search_space, *dependencies))
        random.shuffle(total_space)
        total_space = total_space[:self.max_iter_]
        yield from total_space