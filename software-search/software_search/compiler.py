
class Compiler:

    def __init__(self, name, version=None):
        self.name = name
        if version:
            self.version = version

    
    def get_compiler_spec(self):
        if hasattr(self, 'version'):
            return '{}@{}'.format(self.name, self.version)
        else:
            return '{}'.format(self.name)
    

    def __str__(self):
        return self.get_compiler_spec()