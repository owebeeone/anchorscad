'''
Created on 4 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
from ParametricSolid.extrude import PathBuilder, LinearExtrude
import numpy as np
from anchorscad.models.basic.cone_ended_prism import ConeEndedHull,\
    ConeEndedPrism
    

@core.shape('anchorscad.models.tools.funnel.FilterFunnel.ElipticCone')
@dataclass
class ElipticCone(core.CompositeShape):
    '''
    Cone with an ellipltic cross section on the top side.
    '''
    h: float
    r_base: float
    r_top_x: float
    r_top_y: float
    fn: int=32
    
    
    EXAMPLE_SHAPE_ARGS=core.args(10, 10, 50, 7)
    EXAMPLE_ANCHORS=(
        core.surface_args('top'),
        core.surface_args('base', rh=-1),
        core.surface_args('surface', 0, rh=1, align_scale=True),
        core.surface_args('surface', 0.3, rh=1, align_scale=True),
        core.surface_args('surface', 0.3, rh=0),
        )
    
    def __post_init__(self):
        builder = PathBuilder()
        builder.move((0., self.r_base))
        
        builder.arc_centre_sweep(
            (0.0, 0.0), 
            sweep_angle_degrees=-360.0, 
            name='surface')

        path = builder.build()
        
        scale = (self.r_top_x / self.r_base, self.r_top_y / self.r_base)
       
        shape = LinearExtrude(
            path=path, 
            h=self.h, 
            scale=scale,
            fn=self.fn)
        
        self.maker = shape.solid('eliptic_cone').at()
        
    @core.anchor('top of the shape')
    def top(self):
        return l.tranZ(self.h)

    @core.anchor('base of the shape')
    def base(self, h=0, rh=0):
        return l.tranZ(h + self.h * rh) * l.ROTX_180
        

@core.shape('anchorscad.models.tools.funnel.FilterFunnel.ElipticConeHull')
@dataclass
class ElipticConeHull(core.CompositeShape):
    '''
    A "pipe" with an elliptic cross section on the top end.
    '''
    h: float
    r_base: float
    r_top_x: float
    r_top_y: float
    t: float
    epsilon: float=0.001
    fn: int=32
    
    
    EXAMPLE_SHAPE_ARGS=core.args(10, 10, 50, 7, 1.5)
    EXAMPLE_ANCHORS=(
        core.surface_args('top'),
        core.surface_args('base', rh=-1),
        core.surface_args('surface', 0, rh=1),
        core.surface_args('surface', 0.1, rh=1),
        core.surface_args('surface', 0.3, rh=0),
        )
    
    def __post_init__(self):
        outer = ElipticCone(
            h=self.h,
            r_base=self.r_base,
            r_top_x=self.r_top_x,
            r_top_y=self.r_top_y,
            fn=self.fn)
        
        maker = outer.solid('outer').at('top')
        self.maker = maker
        
        inner = ElipticCone(
            h=self.h + 2 * self.epsilon,
            r_base=self.r_base - self.t,
            r_top_x=self.r_top_x - self.t,
            r_top_y=self.r_top_y - self.t,
            fn=self.fn)
        
        maker.add_at(inner.hole('inner').at('top'),
                     'top', post=l.tranZ(self.epsilon))


def ffs(n):
    '''Returns the bit position of the first (lsb) set bit.'''
    return (n & -n).bit_length() - 1

def radians(degs):
    '''Degrees to radians helper.'''
    return np.pi * degs / 180

@core.shape('anchorscad.models.tools.funnel.FilterFunnel.FilterFunnel')
@dataclass
class FilterFunnel(core.CompositeShape):
    '''Generates a paper filter (classic coffee paper filter) funnel with
    ribs on the inner surface to allow for efficient use of paper filters.
    Args:
        h: Overall paper filter height.
        w: The width of the non cureved section of the paper filter.
        r_base: The outer radius of the round section of the filter.
        r_top: The radius of the small side of the filter.
        t: Wall thickness of the filter shell.
        t_top: Thickness at the small end of the funnel.
        h_rim: Height of the rim on the upper end of the funnel.
        w_rim: The extra width of the funnel rim. (t + w_rim is actual width)
        h_adapter: Overall height of the funnel to tail adapter.
        r_adapter: Radius of the adapter.
        t_adapter: Thickness of the adapter component.
        offs_adapter: The depth the adapter is embedded into the funnel.
        conic_rib_level: Exponent of the number of ribs on the conic sections minus 1.
        rib_factory: A "lazy shape" for rib shapes.
        r_tail: Radius of the lower spout.
        l_tail: Overall length of the tail.
        tail_rib_factory: Factory for ribs on tail.
        n_tail_ribs: Number of tail ribs.
        show_cutaway: Flag for applying a cut section for showing section.
        epsilon: A small value used to overlapping shapes to avoid aliasing
            tears in the final model.
    '''
    h: float=108
    w: float=50
    r_base: float=78 * 2 / np.pi
    r_top: float=1
    t: float=1.5
    t_top: float=t * 2
    # Rim parameters.
    h_rim: float=t
    w_rim: float=5
    
    # Funnel adapter.
    h_adapter: float=25
    r_adapter: float=11.3
    t_adapter: float=2
    offs_adapter: float=10
    
    # Inner ribs.
    conic_rib_level: int=4  # n**2-1 == 15 ribs
    rib_factory: object=core.lazy_shape(
        core.Cone, 'h', 
        other_args=core.args(r_base=1.5 * 1.3, r_top=1.5, fn=3))
    rib_overlap_factor: float=0.016
    
    # Tail pipe
    r_tail: float=8.0
    l_tail: float=40 
    tail_rib_factory: object=core.lazy_shape(
        lambda x, y, z : core.Box((x, y, z)), 'y', 
        other_args=core.args(x=1.5, z=1.5))
    tail_rib_h: float=0.75
    
    n_tail_ribs: int= 6
    
    show_cutaway: bool=False
    epsilon: float=0.001
    fn: int=128
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(
        
        core.surface_args('tail', 'tail_outer', 'surface', rh=0, degrees=60),
        core.surface_args('tail', 'tail_outer', 'surface', rh=1, degrees=60),
        core.surface_args('tail', ('tail_rib', 1), 'face_edge', 1, 2),
        core.surface_args('tail', ('tail_rib', 1), 'face_edge', 1, 0),
#         core.surface_args('base'),
#         core.surface_args('inner', 'prism', 'lside', 0.1, rh=0.6),
#         core.surface_args('inner', 'cone1', 'surface', 0, 180, rh=0.6),
#         core.surface_args('inner', 'cone2', 'surface', 0, 225, rh=0.6),
#         core.surface_args('inner', 'cone2', 'surface', 0, 225, rh=0),
        )
    
    def __post_init__(self):
        
        hull_shape = ConeEndedHull(
            h=self.h, w=self.w, r_base=self.r_base, r_top=self.r_top, 
            t=self.t, t_top=self.t_top, fn=self.fn)
        
        hull = hull_shape.composite('shell').at('top')
        
        r_rim = self.w_rim + self.r_base
        rim = ConeEndedPrism(
            h=self.h_rim, w=self.w, r_base=r_rim, r_top=r_rim, 
            fn=self.fn)
        
        hull.add_at(rim.solid('rim').at('base'), 'base')
        
        self.maker = hull
        
        adapter = ElipticConeHull(
            h=self.h_adapter,
            r_base=self.r_adapter,
            r_top_x=self.r_top + 4,
            r_top_y=self.w / 2 + self.r_top + 4.5,
            t=self.t_adapter,
            fn=self.fn
            )
        hull.add_at(adapter.composite('adapter').at('base', rh=1),
                    'inner', 'top', post=l.tranZ(-self.offs_adapter))

        maker = hull.solid('hull').at()
        self.maker = maker
        
        # Add ribs on the conic surfaces.
        count_conic_side = 2 ** self.conic_rib_level
        degs_per_rib = 180 / count_conic_side
        delta = 1.3
        factor = 1.15
        level_rh = 1 / (delta + self.conic_rib_level)
        max_rh = 1.0
        h = self.t
        rib_pop = self.t * 0.4
        for i in range(1, count_conic_side):
            
            angle = degs_per_rib * i + 180
            rh = (1 + delta + ffs(i) * factor) * level_rh
            if rh > max_rh:
                rh = max_rh
            adj = 0
            for a, rot, pop_size in (
                            ('cone1', l.ROTZ_270, -rib_pop),
                            ('cone2', l.ROTZ_90, rib_pop)):
        
                tran = l.tranY(pop_size + self.epsilon)
                rib_shape = self.rib_factory.solid(('rib', a, i))
                maker.add_between(
                    core.at_spec('inner', a, 'surface', 0, angle, rh=0),
                    core.at_spec('inner', a, 'surface', h, angle, rh=rh),
                    rib_shape,
                    core.at_spec('top', post=rot * tran),
                    core.at_spec('base', post=rot * tran),
                    align_axis=l.X_AXIS,
                    align_plane=l.Z_AXIS
                    )
        
        d = self.r_base * np.sin(radians(degs_per_rib))
        count_flat_side = int(round(0.5 + self.w / d))
        rs = 1 / (count_flat_side - 1)
        h = 0.000001
        tran = l.tranY(rib_pop + self.epsilon)
        for i in range(0, count_flat_side):
            
            w = rs * i
            
            # Inner ribs overlap.
            rl = ((1. + self.rib_overlap_factor) 
                  if i > 0 and i < count_flat_side -1
                  else 0.90)
            
            for a, ts, te in (('lside', rl, 0), ('rside', 1-rl, 1)):
        
                rib_shape = self.rib_factory.solid(('rib', a, i))
                maker.add_between(
                    core.at_spec('inner', 'prism', a, ts, h=h, rh=w),
                    core.at_spec('inner', 'prism', a, te, rh=w),
                    rib_shape,
                    core.at_spec('base', post=l.ROTZ_90 * tran),
                    core.at_spec('top', post=l.ROTZ_90 * tran),
                    align_axis=l.Y_AXIS,
                    align_plane=l.X_AXIS
                    )
                
        # Rib cleaner (removes tips of ribs protruding from base).
        maker.add_at(rim.hole('rib_cleaner').at('top'),
                     'hull', 'rim', 'base', 
                     post=l.ROTX_180 * l.tranZ(self.epsilon))
        
        # Tail pipe
        tail_outer = core.Cone(
            h=self.l_tail,
            r_base=self.r_tail,
            r_top=self.r_adapter,
            fn=self.fn)
        
        tail_inner = core.Cone(
            h=self.l_tail + self.epsilon,
            r_base=self.r_tail - self.t,
            r_top=self.r_adapter - self.t_adapter,
            fn=self.fn)
        
        tail_maker = tail_outer.solid('tail_outer').at('centre')
        tail_maker.add_at(tail_inner.hole('tail_inner').at('centre'),
                          'centre')
        
        tail_degs = 360 / self.n_tail_ribs
        for i in range(self.n_tail_ribs):
            degs = tail_degs * i
            
            rib_shape = core.Box((self.t, self.l_tail, self.tail_rib_h))
            tail_maker.add_at(
                rib_shape.solid(('tail_rib', i)).at('face_edge', 1, 0),
                        'tail_outer', 'surface', rh=1, degrees=degs,
                        post=l.ROTX_180)
#             tail_rib_shape = self.tail_rib_factory.solid(('tail_rib', i))
#             tail_maker.add_between(
#                 core.at_spec('tail_outer', 'surface', rh=1, degrees=degs),
#                 core.at_spec('tail_inner', 'surface', h=0, rh=0, degrees=degs),
#                 tail_rib_shape,
#                 core.at_spec('face_edge', 0, 0),
#                 core.at_spec('face_edge', 0, 2),
#                 align_axis=None,
#                 align_plane=None
#                 )
        
        maker.add_at(tail_maker.composite('tail').at('top'),
                     'adapter', 'base', post=l.ROTX_180)
        
        
        # Debug cut-away
        if self.show_cutaway:
            cut = core.Box([self.r_base, 
                            (self.r_base * 2 + self.w) / 2, 
                            self.h + 2 * self.epsilon])
            
            self.maker.add_at(cut.hole('cut').at(), 'top', 
                        post=l.ROTX_180 * l.tranZ(-self.epsilon))
   



if __name__ == '__main__':
    core.anchorscad_main(False)
