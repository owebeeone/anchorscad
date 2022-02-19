'''
Created on 10 Feb 2021

@author: gianni
'''


from dataclasses import dataclass

from ParametricSolid.core import shape, CompositeShape, non_defaults_dict, Cylinder, args, \
    surface_args, anchorscad_main, Cone, create_from, anchor, Box
from ParametricSolid.extrude import PathBuilder 
from ParametricSolid.linear import tranX, tranY, tranZ, ROTX_180
from anchorscad.models.basic.pipe import Pipe
from anchorscad.models.screws.dims import HoleDimensions, holeMetricDims
from anchorscad.models.screws.holes import SelfTapHole
import numpy as np

RUNNER_EXCLUDE=True

@shape('anchorscad/models/cases/rpi4/side_mount')
@dataclass
class SideMount(CompositeShape):
    h: float
    taper_h: float
    wall_sink_depth: float  # How much this is sunk into the wall it's attached to.
    thru_len: float
    tap_len: float
    access_len: float
    access_dia: float
    bevel_r: float
    counter_sink_overlap: float
    dia: float=2.6
    outer_dia: float=None
    dims: HoleDimensions=None
    outer_delta: float=6
    overlap_delta: float=0.01
    fn: int=None
    fa: float=None
    fs: float=None
    
    
    EXAMPLE_SHAPE_ARGS=args(
        h=10,
        taper_h=3,
        wall_sink_depth=3,
        thru_len=1,
        bevel_r=2,
        tap_len=2,
        access_len=10, 
        access_dia=4.5, 
        counter_sink_overlap=0.5, 
        fn=20)
    
    def __post_init__(self):
        self_tap_hole = create_from(SelfTapHole, self)
        if not self.access_dia:
            self.access_dia = self_tap_hole.outer_dia + self.overlap_delta
        if not self.outer_dia:
            self.outer_dia = self_tap_hole.outer_dia
       
        path = self._make_profle()
        
        box_cage = Box([self.outer_dia, ])
        
        self.maker = maker
        
    def _make_sunk_profle(self): 
        bevel_r = self.bevel_r
        outer_r = self.outer_dia / 2
        centre_offset = bevel_r - self.wall_sink_depth
        
        sin_t = centre_offset / (outer_r + bevel_r)
        cos_t = np.sqrt(1 - sin_t ** 2)
        p1 = [cos_t * outer_r, -sin_t * outer_r]
        p2 = [cos_t * (outer_r + bevel_r), 0]
        
        return (PathBuilder()
            .move([0, 0])
            .line([0, -self.r_sphere], 'edge1')
            .arc_tangent_point(p1, degrees=90, name='sphere')
            .arc_tangent_point(p2, name='bevel')
            .line([0, 0], 'edge2')
            .build())
        
    def _make_proud_profle(self):
        bevel_r = self.bevel_r
        outer_r = self.outer_dia / 2
        assert bevel_r < outer_r, \
            f'bevel radius {bevel_r} must be smaller than access radius {outer_r}.'
        base_width = 2 * bevel_r + outer_r * 2
        pathBuilder = (PathBuilder()
            .move([0, 0])
            .line([bevel_r + outer_r, 0], 'back1')
            .arc_tangent_point([base_width - bevel_r, bevel_r], -180, 'bevel1', self))
        
        if bevel_r < outer_r:
            pathBuilder.line([base_width - bevel_r, outer_r])
        pathBuilder.arc_tangent_point([bevel_r, outer_r], 'access', self)
        if bevel_r < outer_r:
            pathBuilder.line([bevel_r, bevel_r])
        pathBuilder.arc_tangent_point([0, 0], 'bevel0', self)
        return pathBuilder.build()
    
    def _make_profile(self):
        bevel_r = self.bevel_r
        outer_r = self.outer_dia / 2
        wall_sink_depth = self.wall_sink_depth 
        if outer_r - wall_sink_depth < bevel_r:
            return self._make_sunk_profle()
        return self._make_proud_profle()
        
        

if __name__ == "__main__":
    anchorscad_main(False)

        
