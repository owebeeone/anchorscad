'''
Created on 28 Jan 2022

@author: gianni
'''

from dataclasses import dataclass
import platform
import os.path as op

@dataclass
class Locator:
    '''
    Locates the openscad executable on the system.
    '''
    exe_path: str
    is_dev: bool = False

    def find(self) -> bool:
        return self.exe_path if op.isfile(self.exe_path) else None


WINDOWS_PLACES_TO_CHECK=(
    Locator('C:\\Program Files\\OpenSCADDev\\openscad.exe', True),
    Locator('D:\\Program Files\\OpenSCADDev\\openscad.exe', True),
    Locator('C:\\Program Files\\OpenSCAD\\openscad.exe'),
    Locator('D:\\Program Files\\OpenSCAD\\openscad.exe'),
    )

CYGWIN_PLACES_TO_CHECK=(
    Locator('/cygdrive/c/Program Files/OpenSCADDev/openscad.exe', True),
    Locator('/cygdrive/d/Program Files/OpenSCADDev/openscad.exe', True),
    Locator('/cygdrive/c/Program Files/OpenSCAD/openscad.exe'),
    Locator('/cygdrive/d/Program Files/OpenSCAD/openscad.exe'),
    )

MACOS_PLACES_TO_CHECK=(
    Locator("/Applications/OpenSCAD.app/Contents/MacOS/openscad"),
    )

# All unix derived systems.
NIX_PLACES_TO_CHECK=(
    Locator('/usr/bin/openscad'),
    Locator('/usr/local/bin/openscad'),
    Locator('/usr/share/openscad/openscad'),
    )

OS_MAP_PLACES_TO_CHECK=(
    ('Windows', WINDOWS_PLACES_TO_CHECK),
    ('CYGWIN_NT', CYGWIN_PLACES_TO_CHECK),
    ('Darwin', MACOS_PLACES_TO_CHECK),
    ('Linux', NIX_PLACES_TO_CHECK),
    ('FreeBSD', NIX_PLACES_TO_CHECK),
    ('OpenBSD', NIX_PLACES_TO_CHECK),
    ('NetBSD', NIX_PLACES_TO_CHECK),
)

def openscad_exe_location():
    '''Returns the system command string for the openscad executable and
    True if it is a development version.
    '''
    
    this_platform = platform.system()
    
    for platform_name, locators in OS_MAP_PLACES_TO_CHECK:
        if this_platform.startswith(platform_name):
            for locator in locators:
                exe_file = locator.find()
                if exe_file:
                    return exe_file, locator.is_dev
    return 'openscad', False

