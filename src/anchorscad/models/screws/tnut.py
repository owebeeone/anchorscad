'''
Created on 27 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
import anchorscad.models.basic.box_side_bevels as bsb
import numpy as np

epsilon=0.001
epsilon2=2 * epsilon

@core.shape('anchorscad/models/screws/tnut')
@dataclass
class Tnut(core.CompositeShape):
    
    r_t: float=17.6 / 2
    h_t: float=1.2
    r_shaft: float=7.4 / 2
    h_shaft: float=8.5
    bevel_shaft: float=8.5 - 6.3
    h_shaft_extension: float=10
    wing_size: tuple=(3.5, 1.2, 6.5)
    wing_angle: float=70
    left_handed: bool=True
    fn: int=32
    fa: float=None
    fs: float=None
    
    EXAMPLE_SHAPE_ARGS=core.args()
    
    
    def __post_init__(self):
        kwds = {'fn': self.fn, 'fs': self.fs, 'fa': self.fa}
        shaft_cage_shape = core.Cylinder(
            h=self.h_shaft, r=self.r_shaft, **kwds)
        
        maker = shaft_cage_shape.cage('cage').at('base')
        
        base_shape = core.Cylinder(h=self.h_t, r=self.r_t, **kwds)
        
        maker.add_at(base_shape.solid('flat').at('base'),
                     'base')
        bevel_shape = core.Cone(h=self.bevel_shaft + epsilon2, 
                                r_base=self.r_shaft + self.bevel_shaft, 
                                r_top=self.r_shaft, 
                                **kwds)
        maker.add_at(bevel_shape.solid('bevel').at('base'),
                     'flat', 'base', rh=1, h=-epsilon)
        
        h_shaft = self.h_shaft - self.bevel_shaft - self.h_t
        
        shaft_cage_shape = core.Cylinder(
            h=h_shaft, r=self.r_shaft, **kwds)
        
        maker.add_at(shaft_cage_shape.solid('shaft').at('base'),
                     'bevel', 'base', rh=1, h=-epsilon)
        
        shaft_extension = core.Cylinder(
            h=h_shaft, r=self.r_shaft, **kwds)
        
        maker.add_at(shaft_extension.solid('shaft_extension')
                     .colour((1, 0, 0))
                     .at('base'),
                     'shaft', 'base', rh=1, h=-epsilon)
        
        wing_shape = core.Box(self.wing_size)
        angle_shift = (-self.wing_angle 
                       if self.left_handed
                       else self.wing_angle - 180)
        
        for i in range(4):
            maker.add_at(wing_shape.solid(('wing', i))
                         .colour((1, 0, 1))
                         .at('face_corner', 0, 0, 
                             pre=l.rotZ(angle_shift) * l.tranZ(-epsilon)),
                         'flat', 'surface', degrees=i * 360 / 4
                         )
        
        self.maker = maker
        

    @core.anchor('An example anchor')
    def origin(self):
        return self.maker.at('centre')


@core.shape('anchorscad/models/screws/tnut_example')
@dataclass
class TnutExample(core.CompositeShape):
    tnut_type: core.Shape=Tnut
    offs: float=4
    fn: int=128
    fa: float=None
    fs: float=None
    
    def __post_init__(self):
        kwds = {'fn': self.fn, 'fs': self.fs, 'fa': self.fa}
        tnut = self.tnut_type(**kwds)
        
        sizexy = tnut.r_t * 2 + self.offs

        maker = bsb.BoxSideBevels(
            (sizexy, sizexy, tnut.h_shaft), self.offs, **kwds)\
                .solid('model').at('centre')
                
        maker.add_at(tnut.hole('tnut').at('base'),
                     'face_centre', 4,
                     post=l.tranZ(epsilon))

        self.maker = maker

if __name__ == "__main__":
    core.anchorscad_main(False)
    
    
