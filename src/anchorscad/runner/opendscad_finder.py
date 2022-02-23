'''
Created on 28 Jan 2022

@author: gianni
'''

import platform
import os.path as op

WINDOWS_PLACES_TO_CHECK=(
    'C:\\Program Files\\OpenSCAD\\openscad.exe',
    'D:\\Program Files\\OpenSCAD\\openscad.exe',
    )

def openscad_exe_location():
    '''Returns the system command string for the openscad executable.'''
    if platform.system() == 'Windows':
        for p in WINDOWS_PLACES_TO_CHECK:
            if op.isfile(p):
                return p
        raise Exception(f'Could not find OpenSCAD. Please install')
    return 'openscad'


