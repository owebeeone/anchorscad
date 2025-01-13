'''
3D Models for resin printer filter funnels.

Created on 10 Oct 2021

@author: gianni
'''

import anchorscad as ad
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

# Anycubic resin bottle opening.
BOTTLE_INNER_DIA=26
BOTTLE_OUTER_DIA=34.6
BOTTLE_OUTER_LIP_DIA=32.3
BOTTLE_INSERTION_H=25

def determine_params(r, r_inner, t_default, t, name):
    '''Given an outer radius, inner radius, thickness and default 
    thickness, determine the missing parameters.'''
    if r is not None:
        if r_inner is None:
            if t is None:
                assert t_default is not None, f'Cannot determine {name}'
                t = t_default
            r_inner = r - t
        else:
            t = r - r_inner
    else:
        assert r_inner is not None, f'Cannot determine {name}'
        if t is None:
            assert t_default is not None, f'Cannot determine {name}'
            t = t_default
        r = r_inner + t
    return r, r_inner, t
            

@ad.shape
@ad.datatree
class ConePipe(ad.CompositeShape):
    '''
    A hollow cone shape. Will solve for missing parameters if possible.
    '''
    h: float
    r_base: float=None
    r_top: float=None
    h_inner: float=ad.dtfield(init=False)
    r_base_inner: float=None
    r_top_inner: float=None
    t: float=None
    t_base: float=None
    t_top: float=None
    outer_cone_node: ad.Node=ad.ShapeNode(ad.Cone)
    inner_cone_node: ad.Node=ad.ShapeNode(ad.Cone, suffix='_inner')
    epsilon: float=0.005
    fn: int=None
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=10, r_base=5, r_top=4, t=2, fn=128)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        (self.r_base, self.r_base_inner, self.t_base) = determine_params(
             self.r_base, self.r_base_inner, self.t, self.t_base, 'base')
         
        (self.r_top, self.r_top_inner, self.t_top) = determine_params(
             self.r_top, self.r_top_inner, self.t, self.t_top, 'top')

        maker = self.outer_cone_node().solid(
            'outer').at('base')
        
        self.h_inner = self.h + 2 * self.epsilon
        maker.add_at(self.inner_cone_node().hole('inner').at('centre'),
                      'centre')
        
        return maker


@ad.shape
@ad.datatree
class ResinFilterFunnel(ad.CompositeShape):
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
    cone_pipe_node: ad.Node=ad.ShapeNode(ConePipe, 'epsilon')
    
    # Boss for snap fit.
    r_boss: float=3.2 / 2
    h_boss: float=(BOTTLE_OUTER_DIA - BOTTLE_OUTER_LIP_DIA) / 2 - 0.5
    p_boss: float=7.25 - 2
    n_boss: int=3
    fn_boss: int=32
    sphere_node: ad.Node=ad.Node(ConePipe, suffix='_boss')

    show_cutaway: bool=False
    epsilon: float=0.001
     
    EXAMPLE_SHAPE_ARGS=ad.args(show_cutaway=False, fn=64, fn_boss=16)
    EXAMPLE_ANCHORS=()
     
    def build(self) -> ad.Maker:
        
        main_shape = self.cone_pipe_node(
            h=self.h,
            r_base = self.r_inner_base + self.t,
            r_top=self.r_inner_top + self.t,
            t=self.t
            )
        
        maker = main_shape.composite('main').at('base')
        
        # Rim
        
        rim_shape = self.cone_pipe_node(
            h=self.h_rim,
            t=self.t_rim + 10,
            r_base_inner=main_shape.r_base_inner - 10,
            r_top_inner=main_shape.r_base_inner - 10,
            )
        
        maker.add_at(rim_shape.composite('rim').at('base'),
                     'main', 'base')
        
        # Mesh clearance
        mesh_shape = self.cone_pipe_node(
            h=self.h_adapter_mesh,
            r_base=main_shape.r_top,
            t_base=main_shape.t_top,
            r_top=self.r_top_outer_mesh,
            r_top_inner=self.r_top_inner_mesh
            )
        
        maker.add_at(mesh_shape.composite('mesh').at('base'),
                     'main', 'base', rh=1)
        
        # Adapter
        adapter_shape = self.cone_pipe_node(
            h=self.h_adapter,
            r_base=mesh_shape.r_top,
            t_base=mesh_shape.t_top,
            r_top=self.r_top_outer_adapter,
            r_top_inner=self.r_top_inner_adapter
            )
        
        maker.add_at(adapter_shape.composite('adapter').at('base'),
                     'mesh', 'base', rh=1)
            
        # Bottle adapter
        
        bottle_inner_shape = self.cone_pipe_node(
            h=self.h_bottle_inner,
            r_base=self.r_bottle_inner,
            r_base_inner=adapter_shape.r_top_inner,
            r_top_inner=adapter_shape.r_top_inner,
            t_top=self.t_top_bottle_inner
            )
        
        maker.add_at(bottle_inner_shape.composite('bottle_inner_adapter')
                     .at('base'),
                     'adapter', 'base', rh=1)
        
        bottle_outer_shape = self.cone_pipe_node(
            h=self.h_bottle_outer,
            r_base=adapter_shape.r_top,
            r_base_inner=self.r_bottle_outer,
            r_top=adapter_shape.r_top,
            r_top_inner=self.r_bottle_outer,
            )
        
        maker.add_at(bottle_outer_shape.solid('bottle_outer_adapter')
                     .at('base'),
                     'adapter', 'base', rh=1)
        
        maker = maker.solid('resin_funnel').at('top', rh=1)
        
        # Tabs
        
        tab_shape = ad.Box([self.w_tab, self.d_tab, self.h_rim])
        
        maker.add_at(tab_shape.solid('tab1').at('face_edge', 2, 0),
            'surface', angle=self.a_tab1, tangent=False)
        
        maker.add_at(tab_shape.solid('tab2').at('face_edge', 2, 0),
            'surface', angle=self.a_tab2, tangent=False)
        
        # Boss
        
        boss_shape = ad.Sphere(r=self.r_boss, fn=self.fn_boss)
        boss_angle = 360 / self.n_boss
        for i in range(self.n_boss):
            maker.add_at(boss_shape.solid(('boss', i))
                    .at('surface', post=ad.tranZ(-self.h_boss)),
                    'bottle_outer_adapter', 'inner', 
                    'surface', h=self.p_boss, angle=boss_angle * i,
                    post=ad.ROTX_180)
        
        # Debug cut-away
        if self.show_cutaway:
            overall_h = (main_shape.h + mesh_shape.h + adapter_shape.h 
                         + bottle_inner_shape.h)
            cut = ad.Box([main_shape.r_base, 
                            main_shape.r_base, 
                            overall_h + 2 * self.epsilon])
            
            maker.add_at(cut.hole('cut').colour([1, 0, 0, 0.5])
                              .at(), 'base', 
                        post=ad.ROTX_180 * ad.tranZ(-self.epsilon))
   
        return maker

 
if __name__ == '__main__':
    ad.anchorscad_main(False)
