'''
Created on 5 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
import ParametricSolid.extrude as e
import numpy as np


@core.shape('anchorscad.models.basic.cone_ended_prism.ConeEndedPrism')
@dataclass
class ConeEndedPrism(core.CompositeShape):
    '''
    Two cones with a trapezoid connection. Similar to a hull operation
    of two cones.
    Args:
        h: Height of the shape.
        w: Width of the flat section of ConeEndedPrism.
        r_base: Base radius (open end).
        r_top: Top radius.
    '''
    h: float
    w: float
    r_base: float
    r_top: float
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args(110, 50, 33 * 4 / np.pi, 5)
    EXAMPLE_ANCHORS=(
        core.surface_args('top'),
        core.surface_args('base'),
        core.surface_args('cone1', 'top'),
        core.surface_args('cone1', 'base')
        )
    
    def __post_init__(self):
        
        r_max= (self.r_base
                if self.r_base > self.r_top
                else self.r_top)
        size = (r_max * 2, r_max * 2 + self.w, self.h)
        maker = core.Box(size).cage(
            'cage').colour([0, 1, 0, 0.5]).at('centre')
        size_inner = (r_max * 2, self.w, self.h)
        box_inner = core.Box(size_inner).cage('inner_cage').at('centre')
        maker.add(box_inner)
            
        cone = core.Cone(
            h=self.h, r_base=self.r_base, r_top=self.r_top, fn=self.fn)
        
        maker.add_at(cone.solid('cone1').at('base'), 
                     'inner_cage', 'face_edge', 0, 0, post=l.ROTX_90)
        maker.add_at(cone.solid('cone2').at('base'), 
                     'inner_cage', 'face_edge', 3, 2, post=l.ROTX_90)
        
        
        path = (e.PathBuilder()
                    .move((0., 0))
                    .line((-self.r_base, 0), name='lbase')
                    .line((-self.r_top, self.h), name='lside')
                    .line((0, self.h), name='ltop')
                    .line((self.r_top, self.h), name='r_top')
                    .line((self.r_base, 0), name='rside')
                    .line((0, 0), name='rbase')
                    .build())
       
        prism = e.LinearExtrude(
            path=path, 
            h=self.w, 
            fn=self.fn)
        
        maker.add_at(prism.solid('prism').at('lbase', 0), 
                     'cone1', 'base', post=l.ROTX_180)
        
        self.maker = maker

    @core.anchor('top of the shape')
    def top(self):
        return self.at('cage', 'face_centre', 4)

    @core.anchor('base of the shape')
    def base(self):
        return self.at('cage', 'face_centre', 1)


@core.shape('anchorscad.models.basic.cone_ended_prism.ConeEndedHull')
@dataclass
class ConeEndedHull(core.CompositeShape):
    '''
    A "hull" made from ConeEndedPrism.
    Args:
        h: Height of the shape.
        w: Width of the flat section of ConeEndedPrism.
        r_base: Base radius (open end).
        r_top: Top radius.
        t: Thickness of hull wall.
    '''
    h: float
    w: float
    r_base: float
    r_top: float
    t: float
    t_top: float=0
    epsilon: float=0.001
    fn: int=128
    
    EXAMPLE_SHAPE_ARGS=core.args(110, 50, 33 * 4 / np.pi, 4.5, 1.5, 1.5)
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        
        outer = ConeEndedPrism(
            h=self.h, w=self.w, r_base=self.r_base, r_top=self.r_top, 
            fn=self.fn)
        self.outer = outer
        
        t = self.t
        ratio = (self.r_base - self.r_top) / self.h
        if self.t_top:
            inner_r_top = self.r_top + ratio * self.t_top - t
        else:
            inner_r_top = self.r_top - t
        
        
        epsilon = self.epsilon
        inner = ConeEndedPrism(
            h=self.h - self.t_top + epsilon * 2, 
            w=self.w, r_base=self.r_base -t, r_top=inner_r_top, 
            fn=self.fn)
        self.inner = inner
        
        maker = outer.solid('outer').at('centre')
        
        maker.add_at(inner.hole('inner').at('cone1', 'base'),
                     'cone1', 'base', post=l.tranZ(epsilon))

        self.maker = maker


if __name__ == '__main__':
    core.anchorscad_main(False)
