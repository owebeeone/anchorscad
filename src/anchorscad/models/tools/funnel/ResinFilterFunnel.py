'''
Created on 10 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
import numpy as np

# Flat filter dimensions.
FILTER_SIDE_A_LEN=96.578
FILTER_SIDE_B_LEN=103
FILTER_FLAT_AB_LEN=155
FILTER_CIRCUMF=2 * 160 + 2 * 30
FILTER_HOLE_HEIGHT=38
FILTER_HOLE_CIRCUMF=(
    FILTER_HOLE_HEIGHT * FILTER_CIRCUMF / FILTER_SIDE_B_LEN)
FILTER_HEIGHT=np.sqrt(
    FILTER_SIDE_A_LEN ** 2 - (FILTER_CIRCUMF / (np.pi * 4)) ** 2)
FILTER_FUNNEL_HEIGHT=(FILTER_HEIGHT *
    (FILTER_CIRCUMF - FILTER_HOLE_CIRCUMF) / FILTER_CIRCUMF)

# Anycubic resin bottle opening
BOTTLE_INNER_DIA=26
BOTTLE_OUTER_DIA=34.6
BOTTLE_OUTER_LIP_DIA=32.3
BOTTLE_INSERTION_H=25

def determine_params(r, r_inner, t_default, t, name):
    '''Given a outer radius, inner radius, thickness and default 
    thickness, determine the missing parameters.'''
    if not r is None:
        if r_inner is None:
            if t is None:
                assert not t_default is None, f'Cannot determine {name}'
                t = t_default
            r_inner = r - t
        else:
            t = r - r_inner
    else:
        assert not r_inner is None, f'Cannot determine {name}'
        if t is None:
            assert not t_default is None, f'Cannot determine {name}'
            t = t_default
        r = r_inner + t
    return r, r_inner, t
            

@core.shape('anchorscad.models.tools.funnel.ConePipe')
@dataclass
class ConePipe(core.CompositeShape):
    '''
    A hollow cone shape. Will solve for missing parameters if possible.
    '''
    h: float
    r_base: float=None
    r_top: float=None
    r_base_inner: float=None
    r_top_inner: float=None
    t: float=None
    t_base: float=None
    t_top: float=None
    epsilon: float=0.001
    fn: int=128
    
    EXAMPLE_SHAPE_ARGS=core.args(h=10, r_base=5, r_top=4, t=2)
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        (self.r_base, self.r_base_inner, self.t_base) = determine_params(
             self.r_base, self.r_base_inner, self.t, self.t_base, 'base')
         
        (self.r_top, self.r_top_inner, self.t_top) = determine_params(
             self.r_top, self.r_top_inner, self.t, self.t_top, 'top')

        maker = core.Cone(
            h=self.h, 
            r_base=self.r_base, 
            r_top=self.r_top, 
            fn=self.fn).solid(
            'outer').at('base')
            
        inner_cone = core.Cone(
            h=self.h + 2 * self.epsilon, 
            r_base=self.r_base_inner, 
            r_top=self.r_top_inner,  
            fn=self.fn)
        maker.add_at(inner_cone.hole('inner').at('centre'),
                      'centre')
        
        self.maker = maker


@core.shape('anchorscad.models.tools.funnel.ResinFilterFunnel')
@dataclass
class ResinFilterFunnel(core.CompositeShape):
    '''
    Funnel for disposable mesh + paper filters typically used for SLA resin 
    being returned to the resin bottle. This model fits the Anycubic bottle
    and should snap fit onto the groove near the mouth of the bottle.
    '''
    h: float=FILTER_FUNNEL_HEIGHT
    r_inner_base: float=FILTER_CIRCUMF / (2 * np.pi)
    r_inner_top: float=FILTER_HOLE_CIRCUMF / (2 * np.pi)
    l_side: float=FILTER_SIDE_A_LEN
    t: float= 2
    
    # Mesh clearance
    h_adapter_mesh: float=15
    r_top_outer_mesh: float=(BOTTLE_OUTER_DIA - 0.5) / 2 + 2
    r_top_inner_mesh: float=(BOTTLE_OUTER_DIA - 0.5) / 2 
    
    # Adapter from cone to bottle adapter.
    h_adapter: float=10
    r_top_outer_adapter: float=(BOTTLE_OUTER_DIA - 0.5) / 2 + 2
    r_top_inner_adapter: float=(BOTTLE_INNER_DIA - 0.5) / 2 - 2
    
    # Bottle adapter.
    h_bottle_inner: float=BOTTLE_INSERTION_H
    r_bottle_inner: float=(BOTTLE_INNER_DIA - 0.5) / 2
    t_base_bottle_inner: float=3
    t_top_bottle_inner: float=1
    h_bottle_outer: float=12
    r_bottle_outer: float=BOTTLE_OUTER_DIA / 2
    t_bottle_tail: float=2
    
    # Rim
    h_rim: float=2
    t_rim: float=5
    
    # Tabs
    w_tab: float=7
    d_tab: float=5
    a_tab1: float=0
    a_tab2: float=180
    
    # Boss for snap fit.
    r_boss: float=3.2 / 2
    h_boss: float=(BOTTLE_OUTER_DIA - BOTTLE_OUTER_LIP_DIA) / 2 - 0.5
    p_boss: float=7.25 - 2
    n_boss: int=3
    fn_boss: int=32

    show_cutaway: bool=False
    epsilon: float=0.01
    fn: int=128
     
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
     
    def __post_init__(self):
        
        main_shape = ConePipe(
            h=self.h,
            r_base = self.r_inner_base + self.t,
            r_top=self.r_inner_top + self.t,
            t=self.t
            )
        
        maker = main_shape.composite('main').at('base')
        
        # Rim
        
        rim_shape = ConePipe(
            h=self.h_rim,
            t=self.t_rim + 10,
            r_base_inner=main_shape.r_base_inner - 10,
            r_top_inner=main_shape.r_base_inner - 10,
            )
        
        maker.add_at(rim_shape.composite('rim').at('base'),
                     'main', 'base')
        
        # Mesh clearance
        mesh_shape = ConePipe(
            h=self.h_adapter_mesh,
            r_base=main_shape.r_top,
            t_base=main_shape.t_top,
            r_top=self.r_top_outer_mesh,
            r_top_inner=self.r_top_inner_mesh
            )
        
        maker.add_at(mesh_shape.composite('mesh').at('base'),
                     'main', 'base', rh=1)
        
        # Adapter
        adapter_shape = ConePipe(
            h=self.h_adapter,
            r_base=mesh_shape.r_top,
            t_base=mesh_shape.t_top,
            r_top=self.r_top_outer_adapter,
            r_top_inner=self.r_top_inner_adapter
            )
        
        maker.add_at(adapter_shape.composite('adapter').at('base'),
                     'mesh', 'base', rh=1)
            
        # Bottle adapter
        
        bottle_inner_shape = ConePipe(
            h=self.h_bottle_inner,
            r_base=self.r_bottle_inner,
            r_base_inner=adapter_shape.r_top_inner,
            r_top_inner=adapter_shape.r_top_inner,
            t_top=self.t_top_bottle_inner
            )
        
        maker.add_at(bottle_inner_shape.composite('bottle_inner_adapter')
                     .at('base'),
                     'adapter', 'base', rh=1)
        
        bottle_outer_shape = ConePipe(
            h=self.h_bottle_outer,
            r_base=adapter_shape.r_top,
            r_base_inner=self.r_bottle_outer,
            r_top=adapter_shape.r_top,
            r_top_inner=self.r_bottle_outer,
            )
        
        maker.add_at(bottle_outer_shape.solid('bottle_outer_adapter')
                     .at('base'),
                     'adapter', 'base', rh=1)
        
        self.maker = maker.solid('resin_funnel').at('top', rh=1)
        
        # Tabs
        
        tab_shape = core.Box([self.w_tab, self.d_tab, self.h_rim])
        
        self.maker.add_at(tab_shape.solid('tab1').at('face_edge', 2, 0),
            'surface', degrees=self.a_tab1, tangent=False)
        
        self.maker.add_at(tab_shape.solid('tab2').at('face_edge', 2, 0),
            'surface', degrees=self.a_tab2, tangent=False)
        
        # Boss
        
        boss_shape = core.Sphere(r=self.r_boss, fn=self.fn_boss)
        boss_angle = 360 / self.n_boss
        for i in range(self.n_boss):
            self.maker.add_at(boss_shape.solid(('boss', i))
                    .at('surface', post=l.tranZ(-self.h_boss)),
                    'bottle_outer_adapter', 'inner', 
                    'surface', h=self.p_boss, degrees=boss_angle * i,
                    post=l.ROTX_180)
        
        # Debug cut-away
        if self.show_cutaway:
            overall_h = (main_shape.h + mesh_shape.h + adapter_shape.h 
                         + bottle_inner_shape.h)
            cut = core.Box([main_shape.r_base, 
                            main_shape.r_base, 
                            overall_h + 2 * self.epsilon])
            
            self.maker.add_at(cut.hole('cut').colour([1, 0, 0, 0.5])
                              .at(), 'base', 
                        post=l.ROTX_180 * l.tranZ(-self.epsilon))
   
 
if __name__ == '__main__':
    core.anchorscad_main(False)
