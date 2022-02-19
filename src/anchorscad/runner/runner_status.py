'''
Created on 22 Jan 2022

@author: gianni
'''

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Optional
from debugpy.common.json import default

@dataclass_json
@dataclass
class RunnerExampleResults(object):
    '''
    Status type for an example of a shape.
    '''
    example_name: str
    error_str: str='' # '' indicates no error.
    output_file_name: Optional[str]=None
    output_file_size: Optional[int]=None
    error_file_name: Optional[str]=None
    error_file_size: Optional[int]=None
    scad_file: Optional[str]=None
    stl_file: Optional[str]=None
    png_file: Optional[str]=None
    graph_file: Optional[str]=None
    graph_svg_dot_file: Optional[str]=None
    graph_svg_file: Optional[str]=None
    shape_pickle_file: Optional[str]=None
    stl_file: Optional[str]=None


@dataclass_json
@dataclass
class RunnerShapeResults(object):
    '''
    Status type for a shape class run.
    '''
    class_name: str
    examples_with_error_output: int=0
    example_results: List[RunnerExampleResults]=field(default_factory=list)

@dataclass_json
@dataclass
class RunnerModuleExampleRef(object):
    '''
    A reference to a module+example.
    '''
    module_name: str
    class_name: str
    example_name: str
    

@dataclass_json
@dataclass
class RunnerModuleStatus(object):
    '''
    Status type for a module run.
    '''
    module_name: str
    shape_results: List[RunnerShapeResults]
    examples_with_error_output: List[RunnerModuleExampleRef]
    exit_status: Optional[int]=None
    incomplete: bool=False
 
@dataclass_json
@dataclass
class RunnerStatus(object):
    '''
    Status type for a complete run.
    '''
    dirs: List[str]
    elapsed_time: float
    module_status: List[RunnerModuleStatus]
    examples_with_error_output: List[RunnerModuleExampleRef]

   

@dataclass_json
@dataclass
class RunnerModuleStatus2(RunnerModuleStatus):
    other_thing: str=None


example = RunnerModuleStatus(
    'mod_name',
    (RunnerShapeResults('shape1', 
                        (RunnerExampleResults('ex_name11', 'sf', 'gf', 'pf', 'stl'),
                         RunnerExampleResults('ex_name12', 'sf', 'gf', 'pf', 'stl'))),
    RunnerShapeResults('shape2', 
                        (RunnerExampleResults('ex_name21', 'sf', 'gf', 'pf', 'stl'),
                         RunnerExampleResults('ex_name22', 'sf', 'gf', 'pf', 'stl'))),
    ),
    examples_with_error_output=0
    )

def main():
    s = example.to_json(indent=4)
    js = RunnerModuleStatus2.from_json(s)

    print(s)
    print(js)
    print(js.to_json(indent=4))

if __name__ == "__main__":
    main()
