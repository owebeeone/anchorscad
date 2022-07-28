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

CYGWIN_PLACES_TO_CHECK=(
    '/cygdrive/c/Program Files/OpenSCAD/openscad.exe',
    '/cygdrive/d/Program Files/OpenSCAD/openscad.exe',
    )

MACOS_PLACES_TO_CHECK=(
    "/Applications/OpenSCAD.app/Contents/MacOS/openscad",
    )

LINUX_PLACES_TO_CHECK=(
    '/usr/bin/openscad',
    '/usr/local/bin/openscad',
    '/usr/share/openscad/openscad',
    )

OS_MAP_PLACES_TO_CHECK=(
    ('Windows', WINDOWS_PLACES_TO_CHECK),
    ('CYGWIN_NT', CYGWIN_PLACES_TO_CHECK),
    ('Darwin', MACOS_PLACES_TO_CHECK),
    ('Linux', LINUX_PLACES_TO_CHECK),
)

def openscad_exe_location():
    '''Returns the system command string for the openscad executable.'''
    
    this_platform = platform.system()
    
    for platform_name, places_to_check in OS_MAP_PLACES_TO_CHECK:
        if this_platform.startswith(platform_name):
            for place_to_check in places_to_check:
                if op.isfile(place_to_check):
                    return place_to_check
    return 'openscad'

