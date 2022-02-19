'''
Created on 9 Feb 2021

@author: gianni
'''

from dataclasses import dataclass

from ParametricSolid.core import shape, CompositeShape, non_defaults_dict, Cylinder, args,\
    surface_args, anchorscad_main, Cone, create_from, anchor
from ParametricSolid.linear import tranX, tranY, tranZ, ROTX_180
from anchorscad.models.basic.pipe import Pipe
from anchorscad.models.screws.dims import HoleDimensions, holeMetricDims
import numpy as np


@shape('anchorscad/models/screws/holes/self_tap_hole')
@dataclass
class SelfTapHole(CompositeShape):
    thru_len: float
    tap_len: float
    outer_dia: float=None
    dia: object=None
    dims: HoleDimensions=None
    outer_delta: float=6
    overlap_delta: float=0.01
    fn: int=None
    fa: float=None
    fs: float=None
    
    
    EXAMPLE_SHAPE_ARGS=args(thru_len=16, tap_len=8, dia=2.6, fn=20)
    EXAMPLE_ANCHORS=(surface_args('start'), surface_args('bottom'))
    
    def __post_init__(self):
        dims = self.dims
        if not dims:
            dims = holeMetricDims(self.dia)
        outer_dia = self.outer_dia
        if not outer_dia:
            outer_dia = dims.thru_dia + self.outer_delta
            self.outer_dia = outer_dia
        
        params = non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        
        thru_hole = Pipe(
            h=self.thru_len + self.overlap_delta * 2, 
            inside_r=dims.thru_dia / 2, 
            outside_r=outer_dia / 2,
            **params)
        tap_hole = Pipe(
            h=self.tap_len + self.overlap_delta * 2, 
            inside_r=dims.tap_dia / 2,
            outside_r=outer_dia / 2,
            **params)
        cage_cyl = Cylinder(h=self.thru_len + self.tap_len, r=outer_dia / 2)
        maker = cage_cyl.cage('pipe').at('top')
        maker.add_at(thru_hole.composite('thru').at('top'), 'top', pre=tranZ(self.overlap_delta))
        maker.add_at(tap_hole.composite('tap').at('base'), 'base', pre=tranZ(self.overlap_delta))
        
        self.maker = maker
        
    @anchor('The entrance point for screws')
    def start(self):
        return self.maker.at('top')
    
    
    @anchor('The bottom of the screw hole')
    def bottom(self):
        return self.maker.at('base')

@shape('anchorscad/models/screws/holes/countersink_access_hole')
@dataclass
class CountersinkAccessHole(CompositeShape):
    access_len: float
    access_dia: float
    counter_sink_overlap: float
    overlap_delta: float=0.01
    fn: int=None
    fa: float=None
    fs: float=None
    
    
    EXAMPLE_SHAPE_ARGS=args(access_len=10, access_dia=4.5, counter_sink_overlap=0.5, fn=20)
    
    def __post_init__(self):
        params = non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        access_r = self.access_dia / 2
        access_hole = Cylinder(
            h=self.access_len + self.counter_sink_overlap,
            r=access_r,
            **params)

        access_hole_cage = Cylinder(
            h=self.access_len,
            r=access_r,
            **params)
        maker = access_hole_cage.cage('access_hole_cage').at('top')
        maker.add_at(access_hole.hole('access_hole')
                     .at('surface', self.counter_sink_overlap, tangent=False),
                     'surface', 0, tangent=False)
        
        couter_sink_hole = Cone(h=access_r, r_base=0, r_top=access_r, **params)
        
        maker.add_at(couter_sink_hole.hole('couter_sink_hole').colour([1,0,0]).at('surface', access_r, tangent=False),
                     'access_hole', 'surface', self.overlap_delta, tangent=False)
        
        self.maker = maker


@shape('anchorscad/models/screws/holes/countersink_access_hole')
@dataclass
class CountersinkSelfTapHole(CompositeShape):
    '''A self tapped screw hole (two internal diameters) with a extended access hole above
    the screw hole.
    '''
    thru_len: float
    tap_len: float
    access_len: float=1
    access_dia: float=None
    counter_sink_overlap: float=0.5
    outer_dia: float=None
    dia: object=None
    dims: HoleDimensions=None
    outer_delta: float=6
    overlap_delta: float=0.01
    fn: int=None
    fa: float=None
    fs: float=None
    
    
    EXAMPLE_SHAPE_ARGS=args(
        thru_len=10, tap_len=5, access_len=10, 
        access_dia=5, outer_dia=8, dia=2.6, counter_sink_overlap=0.5, fn=180)
    
    def __post_init__(self):
        
        self_tap_hole = create_from(SelfTapHole, self)
        if not self.access_dia:
            self.access_dia = self_tap_hole.outer_dia + self.overlap_delta
        countersink_acccess_hole = create_from(CountersinkAccessHole, self)
        maker = self_tap_hole.composite('screw_hole').at('top')
        self.maker = maker

        maker.add_at(countersink_acccess_hole.composite('access_hole').at('base', post=ROTX_180),
                     'top')


if __name__ == "__main__":
    anchorscad_main(False)
