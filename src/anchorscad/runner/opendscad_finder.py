'''
Created on 28 Jan 2022

@author: gianni
'''

import platform


def openscad_exe_location():
    if platform.system() == 'Windows':
        return 'C:\\Program Files\\OpenSCAD\\openscad.exe'
    return 'openscad'


