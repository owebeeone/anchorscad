'''
Created on 15 Jan 2022

@author: gianni
'''

import argparse
from dataclasses import dataclass, field
import ParametricSolid.core as core
from subprocess import Popen

import sys
import os
import inspect
import os.path as path
import time
import platform
import importlib
import pathlib
import anchorscad.runner.runner_status as rs
from typing import Dict
import pickle
import dill

from anchorscad.runner.opendscad_finder import openscad_exe_location
from anchorscad.runner.process_manager import ProcessManager, ProcessManagerEntry

GENERATE_STL = False

ENVIRON_NAME = '__ANCHORSCAD_RUNNER_KEY__'

PATH_SEPARATOR = ';' if platform.system() == 'Windows' else ':'

OPENSCAD_FILENAME=openscad_exe_location()

def make_openscad_stl_command_line(stl_file, png_file, scad_file):
    stl_options = ('-o', stl_file) if stl_file else ()
    png_options = ('-o', png_file) if png_file else ()
    return (OPENSCAD_FILENAME,) + stl_options + png_options + (
        '--autocenter',
        '--view',
        'axes',
        '--imgsize',
        '1280,1024',
        scad_file
        )

def file_path_splt(fpath):
    if not fpath:
        return ()
    split_path = os.path.split(fpath)
    if split_path[1]:
        return file_path_splt(split_path[0]) + (split_path[1],)
    return ()

def file_path_to_module_path(fpath):
    return '.'.join(file_path_splt(fpath))

def prepend_path(new_entry, curr_path):
    if curr_path is None:
        return new_entry
    path_elems = curr_path.split(PATH_SEPARATOR)
    # Check if new_entry is already found in the current path.
    for p in path_elems:
        if p == new_entry:
            # The current path contains the exact new entry.
            return None, curr_path
        common_prefix = path.commonprefix((p, new_entry))
        if p == common_prefix:
            # The current path contains a prefix.
            return (
                file_path_to_module_path(new_entry[len(common_prefix):]),
                curr_path)
    if new_entry in path_elems:
        path_elems.remove(new_entry)
    return None, PATH_SEPARATOR.join([new_entry] + path_elems)

def file_to_module_and_dir(filename):
    mod_name = path.basename(path.splitext(filename)[0])
    abs_path = path.abspath(filename)
    return mod_name, path.dirname(abs_path)

def add_file_to_path(filename, curr_path):
    mod_name, dir_name = file_to_module_and_dir(filename)
    module_prefix, new_path = prepend_path(dir_name, curr_path)
    if module_prefix:
        return '.'.join((module_prefix, mod_name)), new_path
    return mod_name, new_path


@dataclass
class AnchorScadRunnerEntry(ProcessManagerEntry):
    
    filename: str=None
    mod_name:str =None
    env: dict=None
    as_runner: object=None
    
    def started(self):
        print(f'start: {self.filename}')
        
    def ended(self, status):
        self.as_runner.on_completed(
            filename=self.filename, 
            mod_name=self.mod_name, 
            env=self.env,
            exit_status=status
            )
        

def make_json_status_file(out_dir, module_name):
    '''Makes the filename for the modile RunnerStats file.'''
    return os.path.join(out_dir, 'status-' + module_name + '.json')


@dataclass    
class ExampleRunner:
    out_dir: str
    module_name: str
    out_file_format: str
    runner_results: Dict[str, rs.RunnerShapeResults]=field(default_factory=dict)
    runner_examples: Dict[tuple, rs.RunnerExampleResults]=field(default_factory=dict)
    module_dir: str=None
    status_file_name: str=None
    examples_with_errors: list=field(default_factory=list)
    cumulative_error_text: list=field(default_factory=list)
    
    def __post_init__(self):
        self.module_dir = os.path.sep.join(self.module_name.split('.'))
        
    def get_example_record(self, clz, base_example_name):
        results = self.runner_results.get(clz.__name__, None)
        if not results:
            results = rs.RunnerShapeResults(class_name=clz.__name__)
            self.runner_results[clz.__name__] = results
        
        key = (clz.__name__, base_example_name)
        example = self.runner_examples.get(key, None)
        if not example:
            example = rs.RunnerExampleResults(example_name=base_example_name)
            self.runner_examples[key] = example
            results.example_results.append(example)
        return example, results
        
    def gen_filenames_and_runner(self, clz, example_name, base_example_name, ext):
        rel_filename = self.out_file_format.format(
            module_dir=self.module_dir,
            ext=ext,
            class_name=clz.__name__, 
            example=example_name)
        
        runner_example, _ = self.get_example_record(clz, base_example_name)
        
        fname = os.path.join(self.out_dir, rel_filename)
        full_path = pathlib.Path(fname)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        slash_rel_filename = rel_filename.replace('\\', '/')
        
        return slash_rel_filename, runner_example, full_path
        
    def file_writer(self, obj, clz, example_name, base_example_name):
        rel_filename, runner_example, scad_full_path =\
            self.gen_filenames_and_runner(
                clz, example_name, base_example_name, 'scad')
        runner_example.scad_file = rel_filename
        obj.write(scad_full_path)
        
        stl_rel_filename, runner_example, stl_full_path =\
            self.gen_filenames_and_runner(
                clz, example_name, base_example_name, 'stl')
        runner_example.stl_file = stl_rel_filename
        
        png_rel_filename, runner_example, png_full_path =\
            self.gen_filenames_and_runner(
                clz, example_name, base_example_name, 'png')
        runner_example.png_file = png_rel_filename
        
        if not self.run_openscad(stl_full_path, png_full_path, scad_full_path):
            # Command failed.
            runner_example.png_file = None
            runner_example.stl_file = None
        
    def run_openscad(self, stl_file, png_file, scad_file):
        if not GENERATE_STL:
            stl_file = None
        cmd = make_openscad_stl_command_line(stl_file, png_file, scad_file)
        p = Popen(cmd)
        return p.wait() == 0

    def graph_file_writer(self, graph, clz, example_name, base_example_name):
        
        rel_graph_filename, runner_example, full_graph_path = self.gen_filenames_and_runner(
            clz, example_name, base_example_name, 'dot')
        rel_graph_svg_filename, _, full_svg_path = self.gen_filenames_and_runner(
            clz, example_name, base_example_name, 'svg.dot')
        runner_example.graph_file = rel_graph_filename
        runner_example.graph_svg_dot_file = rel_graph_svg_filename
        runner_example.graph_svg_file = rel_graph_svg_filename + ".svg"

        graph.write_svg(full_svg_path, example_name)
        graph.write(full_graph_path, example_name)
        
    def shape_writer(self, maker, shape, clz, example_name, base_example_name):
        rel_filename, runner_example, full_path = self.gen_filenames_and_runner(
            clz, example_name, base_example_name, 'pickle')
        runner_example.shape_pickle_file = rel_filename
        with open(full_path, 'wb') as f:
            try:
                pickle.dump(shape, f)
            except:
                # Ignore pickling errors for now.
                # Indicate the pickle file is empty,
                runner_example.shape_pickle_file = None
        if runner_example.shape_pickle_file is None:
            try:
                os.remove(full_path)
            except:
                # Just ignore errors when removing files.
                pass
            
    def start_example(self, clz, base_example_name):
        new_stdout = None
        new_stderr = None
        try:
            rel_filename, runner_example, full_path = self.gen_filenames_and_runner(
                clz, base_example_name, base_example_name, 'out.txt')
            runner_example.output_file_name = rel_filename
            self.output_file_name = full_path
            new_stdout = open(full_path, 'w') 
    
            rel_filename, runner_example, full_path = self.gen_filenames_and_runner(
                clz, base_example_name, base_example_name, 'err.txt')
            runner_example.error_file_name = rel_filename
            self.error_file_name = full_path
            new_stderr = open(full_path, 'w') 
            
            self.old_stdout, self.old_stderr,\
            sys.stdout, sys.stderr,\
            new_stdout, new_stderr =\
                sys.stdout, sys.stderr,\
                new_stdout, new_stderr,\
                None, None
            
        finally:
            if new_stdout:
                new_stdout.close()
            if new_stderr:
                new_stderr.close()

    def end_example(self, clz, base_example_name):
        sys.stdout, sys.stderr,\
        new_stdout, new_stderr,\
        self.old_stdout, self.old_stderr=\
            self.old_stdout, self.old_stderr,\
            sys.stdout, sys.stderr,\
            None, None

        if new_stdout:
            new_stdout.close()
        if new_stderr:
            new_stderr.close()
        
        runner_example, runner_results = self.get_example_record(clz, base_example_name)
        runner_example.output_file_size = os.stat(self.output_file_name).st_size
        runner_example.error_file_size = os.stat(self.error_file_name).st_size
        if runner_example.error_file_size:
            runner_results.examples_with_error_output += 1
            self.examples_with_errors.append(
                rs.RunnerModuleExampleRef(
                    module_name=self.module_name,
                    class_name=clz.__name__,
                    example_name=base_example_name))

            with open(self.error_file_name, 'r') as f:            
                self.cumulative_error_text.append(
                    f'Class {self.module_name}.{clz.__name__} '
                    f'example "{base_example_name}"\n------------------\n'
                    + f.read() + '\n')
        

    def write_runner_status(self):
        runner_status = rs.RunnerModuleStatus(
            module_name=self.module_name,
            shape_results=tuple(self.runner_results.values()),
            examples_with_error_output=self.examples_with_errors)
        
        status_file_name = make_json_status_file(
            self.out_dir, self.module_name)
        
        pathlib.Path(status_file_name).parent.mkdir(parents=True, exist_ok=True)
        
        with open(status_file_name, 'w') as f:
            f.write(runner_status.to_json(indent=4))
        self.status_file_name = status_file_name
        return runner_status
    
    def get_error_text(self):
        return '=====================\n'.join(self.cumulative_error_text)
    
@dataclass
class AnchorScadRunnerStats:
    
    completed_with_error_status: int=0
    module_stats: list=field(default_factory=list)
    examples_with_error_output: list=field(default_factory=list)
    

class AnchorScadRunner(core.ExampleCommandLineRenderer):
    
    DESCRIPTION='''\
    Traverses the anchorscad directory and runs all example programs.
    
    '''
    
    EXAMPLE_USAGE='''\

        
    '''
    
    def __init__(self, *args, **kwargs):
        
        core.ExampleCommandLineRenderer.__init__(self, *args, **kwargs)
        this_module = sys.modules[__name__]
        self.env = dict(os.environ)
        self.this_module_file = path.basename(inspect.getfile(this_module))
        self.proc_mgr = ProcessManager()
        self.time_start = 0
        self.time_end = 0
        self.stats = AnchorScadRunnerStats()
    
    def add_more_args(self):
        core.ExampleCommandLineRenderer.add_more_args(self)

        self.argq.add_argument(
            'dirs',
            metavar='dirs',
            type=str,
            nargs='*',
            default=('.',),
            help='List of directories to scan.')
                
        self.argq.add_argument(
            '--no-recursive', 
            dest='recursive',
            action='store_false',
            help='Does not recursively through directories.')
        
        self.argq.add_argument(
            '--recursive', 
            dest='recursive',
            action='store_true',
            help='Recursively pass through directories.')
                
        self.argq.add_argument(
            '--out_file_format', 
            type=str,
            default=os.path.join(
                'output',
                '{module_dir}', 
                'anchorcad_{class_name}_{example}_example.{ext}'),
            help='output format for generated files.')
        
        self.argq.add_argument(
            '--out_dir', 
            type=str,
            default='generated',
            help='output directory.')
        
        self.argq.add_argument(
            '--golden_dir', 
            type=str,
            default='.',
            help='Reference directory used to compare generated files to.')
        
        
        self.argq.set_defaults(recursive=True)

    def run_module(self):
        
        ex_runner = ExampleRunner(
            out_dir=self.argp.out_dir,
            module_name=self.argp.dirs[1],
            out_file_format=self.argp.out_file_format)
        
        core.render_examples(
            self.module, 
            self.options, 
            ex_runner.file_writer,
            ex_runner.graph_file_writer,
            ex_runner.shape_writer,
            ex_runner.start_example,
            ex_runner.end_example)
        
        runner_status = ex_runner.write_runner_status()
        
        # Write all the errors.
        sys.stderr.write(ex_runner.get_error_text())
        
        return runner_status
        
        
    def run(self):
        if ENVIRON_NAME in self.env:
            return self.load_and_run_module()
        ppath_str = self.env.get('PYTHONPATH', None)
        if ppath_str:
            ppath = ppath_str.split(PATH_SEPARATOR)
            norm_ppath = tuple(path.realpath(path.abspath(p)) for p in ppath)
            self.env['PYTHONPATH'] = PATH_SEPARATOR.join(norm_ppath)
        self.time_start = time.time()
        files_seen = set()
        for d in self.argp.dirs:
            for root, subdirs, files in os.walk(d):
                if root.endswith('__pycache__'):
                    continue
                remove_from_list(files, '__init__.py')
                remove_from_list(files, self.this_module_file)
                
                for file in files:
                    if not file.endswith('.py'):
                        continue
                    if file.endswith('_test.py'):
                        continue
                    norm_file = os.path.realpath(path.join(root, file))
                    if norm_file in files_seen:
                        continue
                    files_seen.add(norm_file)
                    # Don't run yourself.
                    
                    self.run_file(norm_file)
                    
        self.proc_mgr.wait_for_completions(0)
        self.time_end = time.time()
        succeeded, failed = self.proc_mgr.finished_status()
        elapsed_time = self.time_end - self.time_start
        runner_status = self.write_runner_status(elapsed_time)
        
        print(f'Total modules = {succeeded + failed}')
        print(f'Failed modules = {failed}')
        print(f'Failed examples = {len(runner_status.examples_with_error_output)}')
        
    def write_runner_status(self, elapsed_time):
        runner_status = rs.RunnerStatus(
            dirs=self.argp.dirs,
            elapsed_time=elapsed_time,
            module_status=self.stats.module_stats,
            examples_with_error_output=self.stats.examples_with_error_output)
        
        filename = os.path.join(self.argp.out_dir, 'status.json')
        pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
        status_json = runner_status.to_json(indent=4)
        with open(filename, 'w') as f:
            f.write(status_json)
        
        return runner_status
        
    
    def load_and_run_module(self):
        module_name = self.argp.dirs[1]
        print(f'file={self.argp.dirs[0]}, module={module_name}')
        try:
            anchorscad_module = importlib.import_module(module_name)
        except Exception as e:
            nl = '\n    '
            sys.stderr.write(
                'ERROR: '
                f'unable to load file={self.argp.dirs[0]}, module={module_name}\n'
                f'PPATH={nl.join(os.environ["PYTHONPATH"].split(";"))}\n')
            raise
        
        if hasattr(anchorscad_module, 'RUNNER_EXCLUDE'):
            if anchorscad_module.RUNNER_EXCLUDE:
                return
        classes = core.find_all_shape_classes(anchorscad_module)
        if not classes:
            return
        
        self.module = anchorscad_module
        self.module_name = module_name
        
        self.run_module()
        
        return
                    
    def run_file(self, filename):
        env = dict(self.env)
        ppath = env.get('PYTHONPATH', None)
        mod_name, new_path = add_file_to_path(filename, ppath)
        if '.examples_out.' in mod_name:
            # Avoid cruft in examples directory.
            return
        env['PYTHONPATH'] = new_path
        env[ENVIRON_NAME] = filename
        
        command = (
            sys.executable,
            self.this_module_file,
            filename,
            mod_name
            )
        
        entry = AnchorScadRunnerEntry(
            filename=filename, mod_name=mod_name, env=env, as_runner=self)
        self.proc_mgr.run_proc(
            entry, command, env=env)
        
    def on_completed(self, filename, mod_name, env, exit_status):
        
        print(f'end: {filename} with status {exit_status}')
        
        status_file_name = make_json_status_file(
            self.argp.out_dir, mod_name)
        
        status_json = None
        try:
            with open(status_file_name, 'r') as f:
                status_json = f.read()
        except:
            pass
        
        if status_json:
            mod_status = rs.RunnerModuleStatus.from_json(status_json)
            mod_status.exit_status = exit_status
            mod_status.incomplete = False
        else:
            mod_status = rs.RunnerModuleStatus(
                mod_name, 
                shape_results=(),
                examples_with_error_output=(),
                exit_status=exit_status,
                incomplete=True)
        
        self.stats.module_stats.append(mod_status)
        self.stats.examples_with_error_output.extend(
            mod_status.examples_with_error_output)



def get_this_module():
    this_module = sys.modules[__name__]
    try:
        return inspect.getfile(this_module)
    except TypeError:
        return None

def remove_from_list(l, v):
    try:
        return l.remove(v)
    except ValueError:
        return
        
def run():
    runner = AnchorScadRunner(sys.argv)
    runner.run()

if __name__ == '__main__':
    run()
