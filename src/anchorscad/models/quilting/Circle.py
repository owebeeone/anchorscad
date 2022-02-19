'''
Created on 18 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
from ParametricSolid.extrude import PathBuilder, LinearExtrude
import numpy as np

INCH=25.4


@core.shape('anchorscad.models.quilting.Circle')
@dataclass
class Circle(core.CompositeShape):
    '''
    A Circle
    '''
    radius: float=1 * INCH
    t: float=1.5
    fn: int=60
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        shape = core.Cylinder(r=self.radius, h=self.t, fn=self.fn)
        
        self.maker = shape.solid("circle").at('base')

if __name__ == '__main__':
    core.anchorscad_main(False)
