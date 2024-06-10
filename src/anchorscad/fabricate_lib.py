'''
Created on 11 Jan 2022

@author: gianni
'''

from dataclasses import dataclass, field
from typing import Dict
from anchorscad.core import DuplicateNameException
from frozendict import frozendict

@dataclass(frozen=True)
class StlRecipeArgs:
    '''Parameters for generating STL files.'''
    enable: bool=True


@dataclass(frozen=True)
class ImageRecipeArgs:
    '''Parameters for generating image files.'''
    enable: bool=True
    imgsize: tuple=(1280, 1024)


@dataclass(frozen=True)
class GraphRecipeArgs:
    '''Parameters for generating image files.'''
    enable: bool=True
    enable_svg: bool=True


@dataclass(frozen=True)
class Recipe:
    '''The shape to 'fabricate' '''
    name: str
    shape_func: object
    anchor: object=None
    place_at: object=None


@dataclass(frozen=True)
class Recipies:
    '''The shape to 'fabricate' '''
    recipies: Dict[str, Recipe]

class RecipiesBuilder:
    def __init__(self):
        self.map = dict()
    
    def add(self, name: str, shape_func: object, *args, **kwds):
        if name in self.map:
            raise DuplicateNameException(
                f'Shape {name} has been added previously.')
        self.map[name] = Recipe(name=name, 
                                shape_func=shape_func,
                                *args, 
                                **kwds)
        return self
    
    def build(self):
        return frozendict(self.map)
        

@dataclass
class Fabricator:
    '''
    Data class of collective fabricator parameters.
    '''
    recipies: Recipies=field(init=False)
    stl_args: StlRecipeArgs=StlRecipeArgs(True)
    image_args: ImageRecipeArgs=ImageRecipeArgs(imgsize=(1280, 1024))
    graph_args: GraphRecipeArgs=GraphRecipeArgs()
    file_basename: str=None # Use the class name if unset.

