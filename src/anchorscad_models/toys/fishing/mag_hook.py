'''
Created on 2025-07-09

@author: gianni

A magentic hook for a child's fishing game.
'''

import anchorscad as ad
from anchorscad_models.basic.regular_prism import RegularPrism
import numpy as np
from anchorscad_models.joins.DoveTail import DoveTail
from anchorscad_models.basic.torus import Torus
from anchorscad_models.screws.holes import CountersinkSelfTapHole


@ad.shape
@ad.datatree
class MagnetCavity(ad.CompositeShape):
    '''
    The cavity for the magnet including the "fishing line" area.
    '''
    r: float=ad.dtfield(13.1 / 2, doc='The radius of the magnet.')
    h: float=ad.dtfield(10, doc='The height of the magnet.')
    line_h: float=ad.dtfield(10, doc='The height of the fishing line cavity.')
    line_r_top: float=ad.dtfield(9 / 2, doc='The radius of the top of the fishing line cavity.')
    hole_r: float=ad.dtfield(4.25 / 2, doc='The radius of the fishing line hole.')
    hole_h: float=ad.dtfield(10, doc='The height of the fishing line hole (protrude out of the hook)')

    mag_node: ad.ShapeNode[ad.Cylinder]
    line_node: ad.ShapeNode[ad.Cone] = ad.dtfield(ad.ShapeNode(ad.Cone, {'r_base': 'r'}, expose_all=True, prefix='line_'))
    hole_node: ad.ShapeNode[ad.Cylinder] = ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='hole_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    @property
    def overall_h(self) -> float:
        return self.h + self.line_h + self.hole_h

    def build(self) -> ad.Maker:
        
        shape = self.mag_node()
        maker = shape.solid('magnet').at('base', post=ad.ROTX_180)
        
        string_shape = self.line_node()
        string_maker = string_shape.solid('string').at('base')
        maker.add_at(string_maker, 'base', rh=1)
        
        hole_shape = self.hole_node()
        hole_maker = hole_shape.solid('hole').at('base')
        maker.add_at(hole_maker, 'string', 'base', rh=1)
        
        return maker
    
@ad.shape
@ad.datatree
class MagnetHook(ad.CompositeShape):
    '''
    The hook containing the magnet.
    '''
    mag_cavity_node: ad.ShapeNode[MagnetCavity]
    mag_cavity_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.mag_cavity_node())
    
    t: float=ad.dtfield(6, doc='The minimum thickness of the hook.')
    base_t: float=ad.dtfield(1, doc='The minimum thickness of the base of the hook.')
    sides: int=ad.dtfield(8, doc='The number of sides of the hook.')
    
    # The radius of the hook.
    mag_hook_r: float=ad.dtfield(self_default=lambda s: s.r + s.t / np.cos(np.pi / (2 * s.sides)))
    mag_hook_base_h: float=ad.dtfield(self_default=lambda s: s.h + s.base_t)
    
    mag_hook_base_node: ad.ShapeNode[RegularPrism] = ad.dtfield(
        ad.ShapeNode(RegularPrism, {'nsides': 'sides', 'r': 'mag_hook_r', 'h': 'mag_hook_base_h'}, expose_all=True, prefix='mag_hook_base_'))
    
    mag_hook_top_h: float=ad.dtfield(self_default=lambda s: s.t + s.line_h)
    
    mag_hook_top_scale: float=ad.dtfield(self_default=lambda s: [s.line_r_top / s.r] * 2)
    
    mag_hook_top_node: ad.ShapeNode[RegularPrism] = ad.dtfield(
        ad.ShapeNode(RegularPrism, {'nsides': 'sides', 'r': 'mag_hook_r'}, expose_all=True, prefix='mag_hook_top_'))
    
    cut_t: float=50
    cut_overall_width: float=35
    cut_overall_height: float=60
    cut_side: bool=False
    cut_dt_edge_width: float=17
    cut_dt_depth: float=2
    cut_dt_widtha: float=4 # Approximate
    cut_dt_widthb: float=3 # Approximate
    cut_edge_shrink: float=0.04

    cut_node: ad.ShapeNode[DoveTail] = ad.dtfield(
        ad.ShapeNode(DoveTail, expose_all=True, prefix='cut_'))

    no_cut: bool=False
    

    fn: int=ad.dtfield(64, doc='The number of facets.')
    
    EXAMPLES_EXTENDED={
        'upper_side': ad.ExampleParams(
            shape_args=ad.args(cut_side=True),
            anchors=()),
        'lower_side': ad.ExampleParams(
            shape_args=ad.args(cut_side=False),
            anchors=()),
    }

    def build(self) -> ad.Maker:
        base_shape = self.mag_hook_base_node()
        
        maker = base_shape.solid('hook').at('base', post=ad.ROTX_180)
        
        mag_hook_top_shape = self.mag_hook_top_node()
        mag_hook_top_maker = mag_hook_top_shape.solid('hook-top').at(('side', 0))
        maker.add_at(mag_hook_top_maker, ('side', 0), rh=1)
        
        cavity_maker = self.mag_cavity_shape.hole('cavity').at('base')
        maker.add_at(cavity_maker, 'base', post=ad.tranZ(-self.base_t))
        
        if not self.no_cut:
            cutter = self.cut_node()
            cutter_maker = cutter.hole('cutter').transparent(False).at('centre', )
            maker.add_at(cutter_maker, 'hook-top', 'base', post=ad.ROTX_90)
        
        return maker
    
    

@ad.shape
@ad.datatree
class MagnetHookWandEnd(ad.CompositeShape):

    no_cut: bool=True
    mag_hook_node: ad.ShapeNode[MagnetHook]
    mag_hook_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.mag_hook_node())
    
    wedge_r_top: float=ad.dtfield(15.8 / 2, doc='The top radius of the wedge.')
    wedge_r_base: float=ad.dtfield(15.95 / 2, doc='The base radius of the wedge.')
    wedge_h: float=ad.dtfield(self_default=lambda s: s.mag_hook_shape.mag_hook_base_h)
    wedge_node: ad.ShapeNode[ad.Cone] = ad.ShapeNode(ad.Cone, expose_all=True, prefix='wedge_')
    
    epsilon: float=ad.dtfield(0.02, doc='The epsilon value.')
    
    EXAMPLES_EXTENDED={
        'small': ad.ExampleParams(
            shape_args=ad.args(wedge_r_top=15.8 / 2, wedge_r_base=15.95 / 2),
            anchors=()),
        'large': ad.ExampleParams(
            shape_args=ad.args(wedge_r_top=19.93 / 2, wedge_r_base=20.08 / 2),
            anchors=()),
    }
    
    def build(self) -> ad.Maker:
        mag_hook_maker = self.mag_hook_shape.solid('hook').at()
        
        wedge_shape = self.wedge_node()
        wedge_maker = wedge_shape.hole('wedge').at('base')
        mag_hook_maker.add_at(wedge_maker, 'hook', 'base', post=ad.tranZ(self.epsilon))
        
        return mag_hook_maker


@ad.shape
@ad.datatree
class MagnetHookOld(ad.CompositeShape):
    '''
    The hook containing the magnet.
    '''
    mag_cavity_node: ad.ShapeNode[MagnetCavity]
    mag_cavity_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.mag_cavity_node())
    
    t: float=ad.dtfield(6, doc='The minimum thickness of the hook.')
    base_t: float=ad.dtfield(1, doc='The minimum thickness of the base of the hook.')
    sides: int=ad.dtfield(8, doc='The number of sides of the hook.')
    
    # The radius of the hook.
    mag_hook_r: float=ad.dtfield(self_default=lambda s: s.r + s.t / np.cos(np.pi / (2 * s.sides)))
    mag_hook_base_h: float=ad.dtfield(self_default=lambda s: s.h + s.base_t)
    
    mag_hook_base_node: ad.ShapeNode[RegularPrism] = ad.dtfield(
        ad.ShapeNode(RegularPrism, {'nsides': 'sides', 'r': 'mag_hook_r', 'h': 'mag_hook_base_h'}, expose_all=True, prefix='mag_hook_base_'))
    
    mag_hook_top_h: float=ad.dtfield(self_default=lambda s: s.t + s.line_h)
    
    mag_hook_top_scale: float=ad.dtfield(self_default=lambda s: [s.line_r_top / s.r] * 2)
    
    mag_hook_top_node: ad.ShapeNode[RegularPrism] = ad.dtfield(
        ad.ShapeNode(RegularPrism, {'nsides': 'sides', 'r': 'mag_hook_r'}, expose_all=True, prefix='mag_hook_top_'))
    
    cut_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.mag_hook_r * 2, s.mag_hook_r, s.mag_cavity_shape.overall_h))
    
    cut_node: ad.ShapeNode[ad.Box] = ad.dtfield(
        ad.ShapeNode(ad.Box, expose_all=True, prefix='cut_'))
    
    rn_r_hole: float=ad.dtfield(self_default=lambda s: s.mag_hook_r - s.t + 1)
    rn_r_section: float=ad.dtfield(2.76 / 2, doc='The radius of the reinforcement section.')
    reinforcement_node: ad.ShapeNode[Torus] = ad.ShapeNode(expose_all=True, prefix='rn_')
    
    key_r: float=ad.dtfield(self_default=lambda s: s.mag_hook_base_h / 4)
    key_h: float=ad.dtfield(self_default=lambda s: s.t / 2 - 0.1)
    key_node: ad.ShapeNode[ad.Cylinder] = ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='key_'))

    
    fn: int=ad.dtfield(64, doc='The number of facets.')

    def build(self) -> ad.Maker:
        base_shape = self.mag_hook_base_node()
        
        maker = base_shape.solid('hook').at('base', post=ad.ROTX_180)
        
        mag_hook_top_shape = self.mag_hook_top_node()
        mag_hook_top_maker = mag_hook_top_shape.solid('hook-top').at(('side', 0))
        maker.add_at(mag_hook_top_maker, ('side', 0), rh=1)
        
        cavity_maker = self.mag_cavity_shape.hole('cavity').at('base')
        maker.add_at(cavity_maker, 'base', post=ad.tranZ(-self.base_t))
        
        cutter = self.cut_node()
        cutter_maker = cutter.hole('cutter').transparent(False).at('face_edge', 'front', 0, post=ad.ROTX_90)
        maker.add_at(cutter_maker, 'hook', 'base', rh=0)
        
        reinforcement_shape = self.reinforcement_node()
        reinforcement_maker = reinforcement_shape.hole(('reinforcement', 0)).colour('red').at('centre')
        maker.add_at(reinforcement_maker, 'hook', 'base', h=self.rn_r_section + 1)
        
        reinforcement_maker = reinforcement_shape.hole(('reinforcement', 1)).colour('pink').at('centre')
        maker.add_at(reinforcement_maker, 'hook', 'base', h=self.rn_r_section + self.mag_hook_base_h - 1)
        
        reinforcement_shape = self.reinforcement_node(r_hole=self.mag_hook_top_scale[0] * self.rn_r_hole)
        reinforcement_maker = reinforcement_shape.hole(('reinforcement', 2)).colour('blue').at('centre')
        maker.add_at(reinforcement_maker, 'hook-top', 'base', h=-self.rn_r_section + self.mag_hook_top_h - 5)
        
        maker = maker.solid('hook-assembled').at('base')
        
        key = self.key_node()
        maker.add_at(key.solid('key-solid').at('centre', post=ad.ROTX_90),
                     'hook-assembled', ('reinforcement', 0), 'centre_start', 
                     post=ad.tranZ((self.mag_hook_base_h - self.rn_r_section) / 2 - 0.5))
        
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
