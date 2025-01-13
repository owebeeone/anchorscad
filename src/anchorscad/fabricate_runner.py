'''
Created on 29 Jan 2022

@author: gianni
'''

import inspect
import sys
from anchorscad_lib.utils.process_manager import ProcessManager, ProcessManagerEntry


def get_fabricator_class(module, name):
    '''Gets the named Fabricator class if it is decorated as @fabricator.
    Returns False otherwise.'''
    
    fv = getattr(module, name)
    if not isinstance(fv, type):
        return False
    if fv.__module__ != module.__name__:
        # Only Fabricators declared in the given module are provided.
        return False
    if not hasattr(fv, 'anchorscad_fabricator') or not hasattr(fv, '__module__'):
        return False
    if fv.anchorscad_fabricator.__class__.__name__ != 'FabricatorParams':
        return False
    return fv

def find_all_fabricators_classes(module):
    '''Returns a list of Fabricator classes (those containing anchorscad_fabricator)
    from the module.
    '''
    fabricator_classes = []
    for name in dir(module):
        shape_class = get_fabricator_class(module, name)
        if shape_class:
            fabricator_classes.append(shape_class)
    return fabricator_classes

__PLATE_SHAPE = None

def get_plate():
    global __PLATE_SHAPE
    
    if __PLATE_SHAPE is None:
        import anchorscad.core as core
        
        class Plate(core.CompositeShape):
            
            def __post_init__(self):
                maker = core.cageof(core.Box([300, 300, 1]), False)
                self.set_maker(maker)
            
            @core.anchor
            def plate(self):
                return self.at('cage', 'face_centre', 1)

        __PLATE_SHAPE = core.shape('anchorscad.fabricator_runner.Plate')(Plate)
    return __PLATE_SHAPE


class FrabricatorRunner:
    
    def __init__(self, runner):
        self.runner = runner
        self.modules = list()
        
    def add(self, fab_module):
        self.modules.append(fab_module)
        
    def run(self):
        for m in self.modules:
            fabricators = find_all_fabricators_classes(m)
            for fab in fabricators:
                self.runner(fab, m)
    
    def runner(self, fab, ):
        pass

class FabricatorSubprocessEntry(ProcessManagerEntry):
    '''Provides the result of the running subprocess.
    '''
    
    def __init__(self, visitor):
        self.visitor = visitor
    
    def ended(self, status):
        if status:
            self.visitor.failed += 1


def run_fabricator(fab):
    
    maker = get_plate().solid().at()
    for recipie in fab.recipies:
        shape = recipie.shape_function()
        
        maker.add_at(
            shape.solid(recipie.name).at(anchor=recipie.anchor),
            anchor=recipie.place_at)
    
    #render maker etc...
    
    


def get_module_file(m):
    try:
        return inspect.getfile(m)
    except TypeError:
        return None
    
class FabricatorSubprocessVisitor:
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.count = 0
        self.failed = 0

        
    def run(self, fab, module):
        file = get_module_file(module)
        self.count += 1
        if not file:
            # The module is not from a file. Execute in line.
            try:
                self.run_recepie(recipie)
            except:
                self.failed += 1
        else:
            
            command_args = (
                file,
                module.__name__,
                fab.__name__
                )
            


def main(argv):
    module_file = argv[1]
    module_name = argv[2]
    fabricator_class_name = argv[3]
    print(f'module_file:{module_file} '
          f'module_name:{module_name} '
          f'fabricator_class_name:{fabricator_class_name}\n')
    return 

if __name__ == "__main__":
    exit(main(sys.argv))
    