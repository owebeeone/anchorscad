'''
Created on 15 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
from ParametricSolid.extrude import PathBuilder, LinearExtrude
import numpy as np

INCH=25.4

@core.shape('anchorscad.models.quilting.dresden')
@dataclass
class DresdenWedge(core.CompositeShape):
    '''
    Creates a template for a Dresden Plate quilt.
    '''
    angle: float=360.0 / 16
    min_w: float=0.75 * INCH
    h: float=7 * INCH
    t: float=3
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={'border': core.ExampleParams(
                            core.args(min_w=0.5 * INCH,
                                      h=7.5 * INCH)),
                       'border_corner': core.ExampleParams(
                            core.args(min_w=0.75 * INCH,
                                      h=10.5 * INCH))}
   
    def __post_init__(self):
        lower_x = self.min_w / 2 
        upper_x = lower_x + np.tan(radians(self.angle / 2)) * self.h
        path = (PathBuilder()
            .move([0, 0])
            .line([-lower_x, 0], 'lower_left')
            .line([-upper_x, self.h], 'left')
            .line([0, self.h], 'upper_left')
            .line([upper_x, self.h], 'upper_right')
            .line([lower_x, 0], 'right')
            .line([0, 0], 'lower_right')
            .build())
        
        shape = LinearExtrude(path=path, h=self.t)
        
        
        self.maker = shape.solid("dresden").at(
            'lower_left', 0, post=l.ROTX_90)
        
@core.shape('anchorscad.models.quilting.dresden')
@dataclass
class DresdenHalfWedge(core.CompositeShape):
    '''
    Creates a half template for a Dresden Plate quilt.
    '''
    angle: float=360.0 / 16
    min_w: float=0.75 * INCH
    h: float=5.75 * INCH
    t: float=3
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        lower_x = self.min_w / 2
        upper_x = lower_x + np.tan(radians(self.angle / 2)) * self.h
        path = (PathBuilder()
            .move([0, 0])
            .line([-lower_x, 0], 'lower_left')
            .line([-upper_x, self.h], 'left')
            .line([0, self.h], 'upper_left')
            .line([0, 0], 'lower_right')
            .build())
        
        shape = LinearExtrude(path=path, h=self.t)
        
        self.maker = shape.solid("dresden").at(
            'lower_left', 0, post=l.ROTX_90)


def radians(degs):
    return np.pi * (degs / 180.0)

@core.shape('anchorscad.models.quilting.dresden')
@dataclass
class DresdenKite(core.CompositeShape):
    '''
    Creates a template for a leaf of a dresden plate quilt.
    '''
    angle: float=360.0 / 16
    min_w: float=0.75 * INCH
    h: float=5.75 * INCH
    t: float=3
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        
        # draw a triangle on extending to the intersection of the 
        # kite side and the y axis. Compute the lengths.
        a1 = self.angle / 2
        a2 = 45
        a3 = 180 - a1 - a2
        
        # Use sine rule to find lengths.
        # https://docs.google.com/document/d/1z8y6XxkwhxLyFvRFRf0xYBrSVRRi6N9ON-V0Xb9OB8Q/edit?usp=sharing
        sa1 = np.sin(radians(a1))
        ta1 = np.tan(radians(a1))
        sa2 = np.sin(radians(a2))
        ca2 = np.cos(radians(a2))
        sa3 = np.sin(radians(a3))
        
        lower_x = self.min_w / 2
        yil = -lower_x / ta1
        
        y1 = self.h - yil
        
        sinerule_ratio = y1 / sa3
        
        la1 = sinerule_ratio * sa1
        
        upper_x = la1 * sa2
        upper_y = self.h - la1 * ca2
        
        self.upper_x = upper_x
        self.upper_y = upper_y
        
        ta1_ac = (upper_x - lower_x) / upper_y
        if np.abs(ta1_ac - ta1) > 1e-10:
            assert (f'Error in computation. tan of a1 ({ta1}) should match'
             + f' the actual {ta1_ac}')
        
        path = (PathBuilder()
            .move([0, 0])
            .line([-lower_x, 0], 'lower_left')
            .line([-upper_x, upper_y], 'left')
            .line([0, self.h], 'upper_left')
            .line([upper_x, upper_y], 'upper_right')
            .line([lower_x, 0], 'right')
            .line([0, 0], 'lower_right')
            .build())
        
        shape = LinearExtrude(path=path, h=self.t)
        
        self.maker = shape.solid("dresden").at(
            'lower_left', 0, post=l.ROTX_90)
        
SEAM_ALLOWANCE = 0.25 * INCH

@core.shape('anchorscad.models.quilting.dresden')
@dataclass
class DresdenBorder(core.CompositeShape):
    '''
    Creates 2 templates for borders.
    '''
    angle: float=360.0 / 16
    min_w: float=0.25 * INCH + SEAM_ALLOWANCE * 2 / np.cos(radians(angle / 2))
    h: float=9.25 * INCH + SEAM_ALLOWANCE * 2
    t: float=3
    render_small: bool=True
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={'small': core.ExampleParams(
                            core.args(render_small=True)),
                       'large': core.ExampleParams(
                            core.args(render_small=False))}
    
    def __post_init__(self):
        # Use DresdenKite to compute upper_y - without seam allowance.
        side_seam_allowance = SEAM_ALLOWANCE / np.cos(radians(self.angle / 2))
        kite = DresdenKite(
            angle=self.angle,
            min_w=self.min_w - 2 * side_seam_allowance,
            h=self.h - 2 * SEAM_ALLOWANCE,
            t=self.t)
        
        upper_y = kite.upper_y
        print(upper_y / INCH)
        if self.render_small:
            shape = DresdenWedge(
                angle=self.angle,
                min_w=2 * side_seam_allowance,
                h=upper_y + 2 * SEAM_ALLOWANCE,
                t=self.t)
            self.maker = shape.maker
        else:
            shape = DresdenWedge(
                angle=self.angle,
                min_w=self.min_w,
                h=self.h,
                t=self.t)
            self.maker = shape.maker

if __name__ == '__main__':
    core.anchorscad_main(False)
