'''
Print the PYTHONPATH to the command line.

Created on 20 Feb 2022

@author: gianni
'''

import platform
from anchorscad.run import PYTHON_PATH, RunAnchorSCADModule

UNIX_FORMAT = '''\
export {env}="{ppath}"
'''

WIN_FORMAT = '''\
For cmd shell:
set {env}="{ppath}"

For powershell:
$env:{env} = '{ppath}'
'''

def main():
    
    rasm = RunAnchorSCADModule()
    
    print(f'\n{PYTHON_PATH} environment variable for AnchorSCAD is')
    
    fmtstr = WIN_FORMAT if platform.system() == 'Windows' else UNIX_FORMAT
    print(fmtstr.format(env=PYTHON_PATH, ppath=rasm.env[PYTHON_PATH]))
    
    print('''\nYou may set these in your IDE to start your IDE with the
    your IDE with python3 src/anchorscad/run.py, e.g. You can start VS Code
    like so:
    
    # Windows
    python3 src/anchorscad/run.py src/anchorscad/run_other.py cmd /c code
    
    # Linux 
    python3 src/anchorscad/run.py src/anchorscad/run_other.py code
    
    ''')
    

if __name__ == '__main__':
    exit(main())