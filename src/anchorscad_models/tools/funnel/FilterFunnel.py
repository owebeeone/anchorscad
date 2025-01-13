'''
Created on 4 Oct 2021

@author: gianni

A funnel for a paper filter.
'''

import anchorscad as ad
import numpy as np
from anchorscad_models.basic.cone_ended_prism import ConeEndedHull,\
    ConeEndedPrism
    

@ad.shape
@ad.datatree
class ElipticCone(ad.CompositeShape):
    '''
    Cone with an ellipltic cross section on the top side.
    '''
    h: float
    r_base: float
    r_top_x: float
    r_top_y: float
    fn: int=32
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(10, 10, 50, 7)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base', rh=-1),
        ad.surface_args('surface', 0, rh=1, align_scale=True),
        ad.surface_args('surface', 0.3, rh=1, align_scale=True),
        ad.surface_args('surface', 0.3, rh=0),
        )
    
    def build(self) -> ad.Maker:
        builder = ad.PathBuilder()
        builder.move((0., self.r_base))
        
        builder.arc_centre_sweep(
            (0.0, 0.0), 
            sweep_angle=-360.0, 
            name='surface')

        path = builder.build()
        
        scale = (self.r_top_x / self.r_base, self.r_top_y / self.r_base)
       
        shape = ad.LinearExtrude(
            path=path, 
            h=self.h, 
            scale=scale,
            fn=self.fn)
        
        return shape.solid('eliptic_cone').at()
        
    @ad.anchor('top of the shape')
    def top(self):
        return ad.tranZ(self.h)

    @ad.anchor('base of the shape')
    def base(self, h=0, rh=0):
        return ad.tranZ(h + self.h * rh) * ad.ROTX_180
        

@ad.shape
@ad.datatree
class ElipticConeHull(ad.CompositeShape):
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
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(10, 10, 50, 7, 1.5)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base', rh=-1),
        ad.surface_args('surface', 0, rh=1),
        ad.surface_args('surface', 0.1, rh=1),
        ad.surface_args('surface', 0.3, rh=0),
        )
    
    def build(self) -> ad.Maker:
        outer = ElipticCone(
            h=self.h,
            r_base=self.r_base,
            r_top_x=self.r_top_x,
            r_top_y=self.r_top_y,
            fn=self.fn)
        
        maker = outer.solid('outer').at('top')
        
        inner = ElipticCone(
            h=self.h + 2 * self.epsilon,
            r_base=self.r_base - self.t,
            r_top_x=self.r_top_x - self.t,
            r_top_y=self.r_top_y - self.t,
            fn=self.fn)
        
        maker.add_at(inner.hole('inner').at('top'),
                     'top', post=ad.tranZ(self.epsilon))
        
        return maker


def ffs(n):
    '''Returns the bit position of the first (lsb) set bit.'''
    return (n & -n).bit_length() - 1


@ad.shape
@ad.datatree
class FilterFunnel(ad.CompositeShape):
    '''Generates a paper filter (classic coffee paper filter) funnel with
    ribs on the inner surface to allow for efficient use of paper filters.
    '''
    
    h: float=ad.dtfield(108, doc='Overall paper filter height.')
    w: float=ad.dtfield(50, doc='The width of the non cureved section of the paper filter.')
    r_base: float=ad.dtfield(78 * 2 / np.pi, 
                             doc='The outer radius of the round section of the filter.')
    r_top: float=ad.dtfield(1, doc='The radius of the small side of the filter.')
    t: float=ad.dtfield(1.5, doc='Wall thickness of the filter shell.')
    t_top: float=ad.dtfield(1.5 * 2, doc='Thickness at the small end of the funnel.')
    # Rim parameters.
    h_rim: float=ad.dtfield(1.5, doc='Height of the rim on the upper end of the funnel.')
    w_rim: float=ad.dtfield(5, 
        doc='The extra width of the funnel rim. (t + w_rim is actual width)')
    
    # Funnel adapter.
    h_adapter: float=ad.dtfield(25, doc='Overall height of the funnel to tail adapter.')
    r_adapter: float=ad.dtfield(11.3, doc='Radius of the adapter.')
    t_adapter: float=ad.dtfield(2, doc='Thickness of the adapter component.')
    offs_adapter: float=ad.dtfield(10, doc='The depth the adapter is embedded into the funnel.')
    
    # Inner ribs. n**2-1 == 15 ribs
    conic_rib_level: int=ad.dtfield(4, 
        doc='Exponent of the number of ribs on the conic sections minus 1.')

    rib_factory: ad.LazyShape=ad.dtfield(ad.lazy_shape(
        ad.Cone, 'h', 
        other_args=ad.args(r_base=1.5 * 1.3, r_top=1.5, fn=3)),
        doc='A "lazy shape" for rib shapes.')
    rib_overlap_factor: float=ad.dtfield(0.016, doc='Amount of overlap between ribs.')
    
    # Tail pipe
    r_tail: float=ad.dtfield(8.0, doc='Radius of the lower spout.')
    l_tail: float=ad.dtfield(40, doc='Overall length of the tail.')
    tail_rib_factory: object=ad.dtfield(ad.lazy_shape(
        lambda x, y, z : ad.Box((x, y, z)), 'y', 
        other_args=ad.args(x=1.5, z=1.5)),
        doc='Factory for ribs on tail.')
    tail_rib_h: float=ad.dtfield(0.75, doc='Height of tail ribs.')
    
    n_tail_ribs: int=ad.dtfield(6, doc='Number of tail ribs.')
    
    show_cutaway: bool=ad.dtfield(False, 
        doc='Flag for applying a cut section for showing section.')
    epsilon: float=ad.dtfield(0.01, 
        doc='A small value used to overlapping shapes to avoid aliasing tears in preview.')
    fn: int=128
    
    EXAMPLE_SHAPE_ARGS=ad.args(show_cutaway=False)
    NOEXAMPLE_ANCHORS=(
        
        ad.surface_args('tail', 'tail_outer', 'surface', rh=0, angle=60),
        ad.surface_args('tail', 'tail_outer', 'surface', rh=1, angle=60),
        ad.surface_args('tail', ('tail_rib', 1), 'face_edge', 1, 2),
        ad.surface_args('tail', ('tail_rib', 1), 'face_edge', 1, 0),
#         ad.surface_args('base'),
#         ad.surface_args('inner', 'prism', 'lside', 0.1, rh=0.6),
#         ad.surface_args('inner', 'cone1', 'surface', 0, 180, rh=0.6),
#         ad.surface_args('inner', 'cone2', 'surface', 0, 225, rh=0.6),
#         ad.surface_args('inner', 'cone2', 'surface', 0, 225, rh=0),
        )
    
    def build(self) -> ad.Maker:
        
        hull_shape = ConeEndedHull(
            h=self.h, w=self.w, r_base=self.r_base, r_top=self.r_top, 
            t=self.t, t_top=self.t_top, fn=self.fn)
        
        hull = hull_shape.composite('shell').at('top')
        
        r_rim = self.w_rim + self.r_base
        rim = ConeEndedPrism(
            h=self.h_rim, w=self.w, r_base=r_rim, r_top=r_rim, 
            fn=self.fn)
        
        hull.add_at(rim.solid('rim').at('base'), 'base')
        
        adapter = ElipticConeHull(
            h=self.h_adapter,
            r_base=self.r_adapter,
            r_top_x=self.r_top + 4,
            r_top_y=self.w / 2 + self.r_top + 4.5,
            t=self.t_adapter,
            fn=self.fn
            )
        hull.add_at(adapter.composite('adapter').at('base', rh=1),
                    'inner', 'top', post=ad.tranZ(-self.offs_adapter))

        maker = hull.solid('hull').at()
        
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
                            ('cone1', ad.ROTZ_270, -rib_pop),
                            ('cone2', ad.ROTZ_90, rib_pop)):
        
                tran = ad.tranY(pop_size + self.epsilon)
                rib_shape = self.rib_factory.solid(('rib', a, i))
                maker.add_between(
                    ad.at_spec('inner', a, 'surface', 0, angle, rh=0),
                    ad.at_spec('inner', a, 'surface', h, angle, rh=rh),
                    rib_shape,
                    ad.at_spec('top', post=rot * tran),
                    ad.at_spec('base', post=rot * tran),
                    align_axis=ad.X_AXIS,
                    align_plane=ad.Z_AXIS
                    )
        
        d = self.r_base * np.sin(ad.to_radians(degs_per_rib))
        count_flat_side = int(round(0.5 + self.w / d))
        rs = 1 / (count_flat_side - 1)
        h = 0.000001
        tran = ad.tranY(rib_pop + self.epsilon)
        for i in range(0, count_flat_side):
            
            w = rs * i
            
            # Inner ribs overlap.
            rl = ((1. + self.rib_overlap_factor) 
                  if i > 0 and i < count_flat_side -1
                  else 0.90)
            
            for a, ts, te in (('lside', rl, 0), ('rside', 1-rl, 1)):
        
                rib_shape = self.rib_factory.solid(('rib', a, i))
                maker.add_between(
                    ad.at_spec('inner', 'prism', a, ts, h=h, rh=w),
                    ad.at_spec('inner', 'prism', a, te, rh=w),
                    rib_shape,
                    ad.at_spec('base', post=ad.ROTZ_90 * tran),
                    ad.at_spec('top', post=ad.ROTZ_90 * tran),
                    align_axis=ad.Y_AXIS,
                    align_plane=ad.X_AXIS
                    )
                
        # Rib cleaner (removes tips of ribs protruding from base).
        maker.add_at(rim.hole('rib_cleaner').at('top'),
                     'hull', 'rim', 'base', 
                     post=ad.ROTX_180 * ad.tranZ(self.epsilon))
        
        # Tail pipe
        tail_outer = ad.Cone(
            h=self.l_tail,
            r_base=self.r_tail,
            r_top=self.r_adapter,
            fn=self.fn)
        
        tail_inner = ad.Cone(
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
            
            rib_shape = ad.Box((self.t, self.l_tail, self.tail_rib_h))
            tail_maker.add_at(
                rib_shape.solid(('tail_rib', i)).at('face_edge', 1, 0),
                        'tail_outer', 'surface', rh=1, angle=degs,
                        post=ad.ROTX_180)
#             tail_rib_shape = self.tail_rib_factory.solid(('tail_rib', i))
#             tail_maker.add_between(
#                 ad.at_spec('tail_outer', 'surface', rh=1, angle=degs),
#                 ad.at_spec('tail_inner', 'surface', h=0, rh=0, angle=degs),
#                 tail_rib_shape,
#                 ad.at_spec('face_edge', 0, 0),
#                 ad.at_spec('face_edge', 0, 2),
#                 align_axis=None,
#                 align_plane=None
#                 )
        
        maker.add_at(tail_maker.composite('tail').at('top'),
                     'adapter', 'base', post=ad.ROTX_180)
        
        
        # Debug cut-away
        if self.show_cutaway:
            cut = ad.Box([self.r_base, 
                            (self.r_base * 2 + self.w) / 2, 
                            self.h + 2 * self.epsilon])
            
            maker.add_at(cut.hole('cut').at(), 'top', 
                        post=ad.ROTX_180 * ad.tranZ(-self.epsilon))
   

        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == '__main__':
    ad.anchorscad_main(False)
