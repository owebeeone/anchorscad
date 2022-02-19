#!/usr/bin/env python3
'''
Command line runner for AnchorSCAD models or any Python script using 
AnchorSCAD imports.

The AnchorSCAD root directory is applied to the PYTHONPATH and subsequent
parameters are passed to run of the subsequent file in the command line.

Also, the current working directory is changed to the same directory as 
the file being executed.

Example:
  python3 src\\anchorscad\\run.py \\
    src\\anchorscad\\models\\basic\\box_cylinder.py --write --svg_write

    - The src\\anchorscad\\models\\basic\\examples_out directory will contain
      the resulting files.

Created on 17 Feb 2022

@author: gianni
'''

from dataclasses import dataclass, field
import inspect
import os
from pathlib import Path
import platform
from subprocess import Popen
import sys

try:
    import pythonopenscad as posc
    POSC_AVAIL = True
except:
    POSC_AVAIL = False
    

PATH_SEPARATOR = ';' if platform.system() == 'Windows' else ':'
PYTHON_PATH = 'PYTHONPATH'
ANCHORSAD_RUNNER_TAG = 'ANCHORSAD_RUNNER_TAG'

DO_LOG = False

def log_message(message):
    '''Minimal log function.'''
    if DO_LOG:
        sys.stderr.write(message + '\n')
        
        
class MissingPythonOpenScad(Exception):
    '''Could not find module pythonopenscad.'''
        
OTHER_POSC_LOCATIONS=(
    Path('../pythonopenscad/src/pythonopenscad/'),
    Path('../../pythonopenscad/src/pythonopenscad/'),
    )
def find_posc(path_to_module, relative_dirs=OTHER_POSC_LOCATIONS):
    '''If pythonopenscad is not in the path, look for it in some other
    location and if found, return it's path. If pythonopenscad is able
    to load, return None.'''
    if POSC_AVAIL:
        return None  # Nothing needs to be done.
    for p in OTHER_POSC_LOCATIONS:
        posc_path = Path(path_to_module, p)
        if posc_path.is_dir():
            return os.path.abspath(posc_path.parents[0])
    
    raise MissingPythonOpenScad('Unable to import pythonopenscad')

@dataclass
class RunAnchorSCADModule:
    f'''Prepares the environment to contain the appropriate {PYTHON_PATH}
    to execute anchorscad modules.'''
    module: type=sys.modules[__name__]
    env: dict=field(default_factory=lambda : dict(os.environ))
    argv: list=field(default_factory=lambda : list(sys.argv))
    
    def __post_init__(self):
        # Fix PYTHONPATH to AnchorSCAD's root
        ad_path = self.get_anchorscad_path()
        ppath = self.env.get(PYTHON_PATH, None)
        
        self.python_path_ok = False
        if ppath:
            ppath_list = list(Path(i) for i in ppath.split(PATH_SEPARATOR))
            if not ad_path in ppath_list:
                ppath_list.append(ad_path)
                new_ppath = PATH_SEPARATOR.join(str(p) for p in ppath_list)
                log_message(new_ppath)
                self.env[PYTHON_PATH] = new_ppath
                log_message(f"set new ppath to {self.env['PYTHONPATH']}")
            else:
                # PYTHONPATH is set correctly.
                self.python_path_ok = True
        else:
            self.env[PYTHON_PATH] = str(ad_path)
            
        posc_path = find_posc(self.get_anchorscad_path())
        if posc_path:
            self.python_path_ok = False
            ppath = self.env.get(PYTHON_PATH, None)
            if ppath:
                ppath_list = list(Path(i) for i in ppath.split(PATH_SEPARATOR))
                ppath_list.append(posc_path)
                
                new_ppath = PATH_SEPARATOR.join(str(p) for p in ppath_list)
                log_message(new_ppath)
                self.env[PYTHON_PATH] = new_ppath
            else:
                self.env[PYTHON_PATH] = str(posc_path.parents[1])

    
    def run(self):
        if self.python_path_ok:
            return self.run_ad_command()
        
        if self.env.get(ANCHORSAD_RUNNER_TAG, None) == 'T':
            sys.stderr.write(
                f'Error: {ANCHORSAD_RUNNER_TAG} environment variable is set. '
                f'This indicates a failure to properly set {PYTHON_PATH}.')
            return 1
        
        command = (
            sys.executable,
            inspect.getfile(self.module),
            ) + tuple(self.argv[1:])
        
        self.env[ANCHORSAD_RUNNER_TAG] = 'T'
        
        log_message('Rerunning process.')
        return Popen(command, env=self.env).wait()
    
    def run_ad_command(self):
        if len(self.argv) <= 1:
            sys.stderr.write(
                'Missing command line arg: Python file to execute. ')
            return 1
        
        arg_path = self.argv[1]
        if not os.path.isfile(arg_path):
            sys.stderr.write(
                f'Error: first parameter, "{arg_path}", is not a file path.')
            return 1

        os.chdir(os.path.dirname(arg_path))
        command = (
            sys.executable,
            os.path.basename(arg_path),
            ) + tuple(self.argv[2:])
            
        log_message("run command")
        return Popen(command, env=self.env).wait()
        
    def get_anchorscad_path(self):
        '''Evaluates the AnchorSCAD path given the file location of
        self.module.'''
        path_to_module = Path(inspect.getfile(self.module))
        return path_to_module.parents[1]
    
        
def main():
    runner = RunAnchorSCADModule()
    return runner.run()

if __name__ == '__main__':
    sys.exit(main())
