'''
Created on 4 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
from ParametricSolid.extrude import PathBuilder, LinearExtrude
import ParametricSolid.linear as l
import numpy as np

INCH=25.4

def radians(degs):
    return degs * np.pi / 180

@core.shape('anchorscad.models.quilting.Hexagons')
@dataclass
class HalfHexagon(core.CompositeShape):
    '''
    <description>
    '''
    small_r: float=None
    large_r: float=None
    t: float=3.0
    
    DEFAULT_SMALL_R = 3 * INCH
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        
        if self.large_r is None and self.small_r is None:
            self.small_r = self.DEFAULT_SMALL_R
            
        if not self.small_r is None:
            self.large_r = self.small_r / np.cos(radians(30))
        else:
            self.small_r = self.large_r * np.cos(radians(30))
            
        ypos2 = self.large_r * np.sin(radians(30))
        
        path = (PathBuilder()
            .move([0, 0])
            .line([0, self.large_r], 'upper_side')
            .line([self.small_r, ypos2], 'edge1')
            .line([self.small_r, -ypos2], 'edge2')
            .line([0, -self.large_r], 'edge3')
            .line([0, 0], 'lower_side')
            .build())
        
        shape = LinearExtrude(path, h=self.t)
        
        self.maker = shape.solid('half_hexagon').at(
            'upper_side', 0, post=l.ROTX_270)
        

if __name__ == '__main__':
    core.anchorscad_main(False)
