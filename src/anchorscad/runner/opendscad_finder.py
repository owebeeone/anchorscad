'''
Created on 28 Jan 2022

@author: gianni
'''

from dataclasses import dataclass, field
import platform
import os.path as op
from subprocess import Popen, PIPE
import re
import os
import datetime
import pickle
from typing import Dict

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

# Matches the --enable flag in the openscad --help output.
HELP_ENABLE_REGEX_PATTERN = re.compile(
    r'.*--enable[^:]+:((?:[\s\n\r]*\s*[a-zA-Z0-9]+(?:-?[a-zA-Z0-9]+)+[\s\n\r]*\|*[\s\n\r]*)*).*',
    re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class OpenscadExeSignature:
    exe: str
    modified: datetime.datetime
    size: int

    @staticmethod
    def from_exe(exe_file: str) -> 'OpenscadExeSignature':
        '''Returns a signature for the given openscad executable.'''
        file_info = os.stat(exe_file)
        file_size = file_info.st_size
        last_modified = datetime.datetime.fromtimestamp(file_info.st_mtime)
        return OpenscadExeSignature(exe_file, last_modified, file_size)
    
    @staticmethod
    def make_default(name: str='openscad') -> 'OpenscadExeSignature':
        '''Returns a default signature.'''
        return OpenscadExeSignature(name, datetime.datetime.min, 0)


@dataclass(frozen=True)
class OpenscadProperties:
    '''Properties of the openscad executable.'''
    signature: OpenscadExeSignature
    features: set
    
    @staticmethod
    def from_features_exe(features: set, exe_file: str) -> 'OpenscadProperties':
        '''Returns OpenscadProperties.'''
        
        return OpenscadProperties(
            OpenscadExeSignature.from_exe(exe_file),
            features)
            
    def is_exe_signature_matching(self, exe_file: str) -> bool:
        signature = OpenscadExeSignature.from_exe(exe_file)
        return self.signature == signature
    
    @staticmethod
    def make_default(name: str='openscad') -> 'OpenscadProperties':
        '''Returns a default OpenscadProperties. This is for cases where openscad can't be found
        in the usual places. It is likely to that openscad is not installed.'''
        return OpenscadProperties(
            OpenscadExeSignature.make_default(name),
            set())
    
    @property
    def exe(self) -> str:
        return self.signature.exe
    


@dataclass
class CachedData:
    '''Data stored in the cache file.'''
    openscad_exe_properties: Dict[str, OpenscadProperties] = field(default_factory=dict)


def store_cache(data, filename=".anchorscad_cache"):
    """Cache data to a file in the user's home directory."""
    cache_file = os.path.join(os.path.expanduser("~"), filename)
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)

def load_cache(filename=".anchorscad_cache", clazz=CachedData):
    """Load data from a cache file in the user's home directory."""
    cache_file = os.path.join(os.path.expanduser("~"), filename)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
                if isinstance(result, clazz):
                    return result
        except:
            pass
    return clazz()  # retirn an empty cache entry if not loaded.
    
def get_features_from_exe(exe_file: str) -> set:
    # run the exe with --help and check for the --enable flag.
    
    popen = Popen(
        args=['openscad', '--help'], 
        executable=exe_file,
        stdout=PIPE,
        stderr=PIPE)
    _, stderr_out = popen.communicate()
    
    popen.wait()
    
    help_str = stderr_out.decode('utf-8') if stderr_out else ''
    
    match = HELP_ENABLE_REGEX_PATTERN.match(help_str)
    
    if match:
        features_str = match.group(1)
        features_set = set(feature.strip() for feature in features_str.split('|'))
        return features_set


def get_openscad_exe_properties(exe_file: str) -> OpenscadProperties:
    '''Finds properties of the openscad executable.'''
    
    # Load the cache and check if the exe file is in it.
    cache = load_cache()
    
    if exe_file in cache.openscad_exe_properties:
        properties = cache.openscad_exe_properties[exe_file]
        if properties.is_exe_signature_matching(exe_file):
            return properties
       
    features = get_features_from_exe(exe_file) 
    properties = OpenscadProperties.from_features_exe(features, exe_file)
    
    # Store the properties in the cache.
    cache.openscad_exe_properties[exe_file] = properties
    
    store_cache(cache)
    
    return properties

def openscad_exe_properties():
    '''Returns the system command string for the openscad executable and
    True if it is a development version.
    '''
    
    this_platform = platform.system()
    
    for platform_name, locators in OS_MAP_PLACES_TO_CHECK:
        if this_platform.startswith(platform_name):
            for locator in locators:
                exe_file = locator.find()
                if exe_file:
                    return get_openscad_exe_properties(exe_file)
    return OpenscadProperties.make_default()


if __name__ == '__main__':
    print(openscad_exe_properties())