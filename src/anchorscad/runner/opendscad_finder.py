'''
Created on 28 Jan 2022

@author: gianni
'''

import platform


def openscad_exe_location():
    '''Returns the system command string for the openscad executable.'''
    if platform.system() == 'Windows':
        # TODO - Look for other places.
        return 'C:\\Program Files\\OpenSCAD\\openscad.exe'
    return 'openscad'


