'''
Created on 27 Jan 2022

@author: adrian
'''

from typing import Tuple
import anchorscad as ad
from anchorscad import datatree, Node, PathBuilder, LinearExtrude, Path
import numpy as np


def to_2d(gvec) -> np.ndarray:
    return gvec.A[0:2]

INNER_CYL_R = 41.6 / 2
OUTER_CYL_R = 50 / 2

INNER_CYL_THICKNESS = 4.15
OUTER_CYL_THICKNESS = 1.95

TAB_WITDH = 20.2 - 4
TAB_DEPTH = 2.65 - .25

KEY_HEIGHT = 2.5
KEY_THICKNESS = 2.5
KEY_OFFSET = 44.68 - INNER_CYL_R * 2

    
@ad.shape
@datatree
class LockTabsAssembly(ad.CompositeShape):
    inner_h: float=INNER_CYL_THICKNESS
    inner_r: float=INNER_CYL_R
        
    outer_h: float=OUTER_CYL_THICKNESS
    outer_r: float=OUTER_CYL_R
    
    tab_depth: float=TAB_DEPTH
    edge_dist: float=ad.dtfield(self_default=lambda s: s.outer_r + s.tab_depth)
    half_tab: float=TAB_WITDH / 2
    
    tab_sweep_radians: float=ad.dtfield(
        self_default=lambda s: 2 * np.arcsin(((s.half_tab) / s.inner_r) / 2))
    
    tab_arc_sweep_radians: float=ad.dtfield(
        self_default=lambda s: 2 * np.arcsin(((s.half_tab - 4.5 / 2) / s.inner_r) / 2))
    
    half_tab_sweep_rotation: ad.GMatrix=ad.dtfield(
        self_default=lambda s: ad.rotZ(radians=s.tab_sweep_radians))
    
    tab_bevel_end_point: np.ndarray=ad.dtfield(
        self_default=lambda s: to_2d(s.half_tab_sweep_rotation * ad.GVector([0, s.outer_r, 0])))
    
    tab_bevel_control_point: np.ndarray=ad.dtfield(
        self_default=lambda s: to_2d(s.half_tab_sweep_rotation * ad.GVector([0, s.edge_dist, 0])))
    
    EPSILON = 0.001 
    
    path: ad.Path=ad.dtfield(
        self_default=lambda s: (PathBuilder()
          .move([0,0], name='origin')
          .line([0, s.edge_dist], 'centre_to_edge')
          .arc_centre_sweep([0,0], sweep_angle=ad.angle(radians=s.tab_arc_sweep_radians), 
                            name='tab_arc')
          .spline(
              (s.tab_bevel_control_point, s.tab_bevel_end_point), 
              cv_len=(2, 1),
              name='tab_corner_curve')
          .line([0, 0], 'edge_to_centre')
          .build()))
    
    h: float=OUTER_CYL_THICKNESS
    
    extrude_node: Node=ad.ShapeNode(LinearExtrude, {'h': 'outer_h'}, 'path')
    cyl_tab_cage_node: Node=ad.ShapeNode(ad.Cylinder, {'h': 'outer_h', 'r': 'edge_dist'})
    cyl_tab_cage: Node=Node(ad.cageof, prefix='cyl_tab_cage_')
    
    fn: int=32
    
    KEY_ANCHOR=ad.surface_args(
        ('tab', 0), 'half_tab_wedge', 'tab_arc', 0)
    
    EXAMPLE_ANCHORS=(ad.surface_args('key'),
                     ad.surface_args(
                         ('tab', 1), 'half_tab_wedge', 'tab_arc', 0))
    EXAMPLE_SHAPE_ARGS=ad.args(cyl_tab_cage_hide_cage=False)
    
    def build(self):
        shape = self.extrude_node()
        
        tab = shape.solid('half_tab_wedge')\
            .at('centre_to_edge', 0, rh=0.5, pre=ad.tranX(self.EPSILON))
        
        tab.add_at(shape.solid('flipped_half_tab_wedge').
                     at('centre_to_edge', 0, rh=0.5, 
                        post=ad.ROTX_180, 
                        pre=ad.tranX(-self.EPSILON)),
                     'centre_to_edge', 0, rh=0.5)
        
        self.cyl_tab_cage_shape = self.cyl_tab_cage_node()
        maker = self.cyl_tab_cage().at('centre')
        
        for i in range(3):
            maker.add_at(tab.solid(('tab', i)).at('tab_arc', 0, rh=0.5), 
                     'surface', angle=i * 120, rh=0.5)
        
        return maker   
    
    @ad.anchor('key mount axis')
    def key(self, tab=0):
        return self.at(('tab', tab), 'half_tab_wedge', 'tab_arc', 0)
    
@ad.shape
@datatree
class CapAndLockAssembly(ad.CompositeShape):

    tabs_node: Node=ad.ShapeNode(LockTabsAssembly)
    inner_cyl_node: Node=ad.ShapeNode(ad.Cylinder, prefix='inner_')
    outer_cyl_node: Node=ad.ShapeNode(ad.Cylinder, prefix='outer_')  

    key_height: float=KEY_HEIGHT
    key_thickness: float=KEY_THICKNESS
    key_offset: float=KEY_OFFSET

    key_size: tuple=ad.dtfield(
        self_default=lambda s: (s.key_thickness, s.key_height, s.key_offset * 2))
    key_node: Node=ad.ShapeNode(ad.Box, prefix='key_')
    
    cap_cage_shape: ad.Shape=None
    cap_cage: Node=Node(ad.cageof, prefix='cap_cage_')
    
    thumbhole_r_base: float=7
    thumbhole_r_top: float=8.5
    thumbhole_h: float=INNER_CYL_THICKNESS + OUTER_CYL_THICKNESS
    
    thumbhole_node: Node=ad.ShapeNode(ad.Cone, prefix='thumbhole_')
    
    fn: int=128
    
    EXAMPLE_ANCHORS=()
    EXAMPLE_SHAPE_ARGS=ad.args(cap_cage_hide_cage=True)
    
    
    def build(self):
        self.cap_cage_shape = ad.Cylinder(
            h=self.outer_h + self.inner_h, r=self.outer_r)
        
        maker = self.cap_cage().at('centre', post=ad.ROTX_180)
        
        inner_cyl = self.inner_cyl_node()
        
        maker.add_at(inner_cyl.solid('inner_cyl').at('base'), 'base')
        
        outer_cyl = self.outer_cyl_node()
        
        maker.add_at(outer_cyl.solid('outer_cyl').at('top'), 'top')
        
        tabs = self.tabs_node()
        
        maker.add_at(tabs.solid('tabs').at('base'), 'outer_cyl', 'base')
        
        key = self.key_node()
        
        maker.add_at(key.solid('key').at('face_edge', 4, 2, 
                                         post=ad.ROTZ_180 * ad.tranZ(self.key_offset)), 
                                         'tabs', 'key')
        
        thumbhole = self.thumbhole_node()
        
        for i in range(3):
            maker.add_at(thumbhole.hole(('thumb', i)).at('base'), 
                         'tabs', 'key', i, post=ad.ROTX_270 * ad.tranY(17) * ad.tranZ(3))
        
        return maker    

@ad.shape
@datatree
class SensorCap(ad.CompositeShape):
    assembly_node: Node=ad.ShapeNode(CapAndLockAssembly)

    EXAMPLE_SHAPE_ARGS=ad.args(fn=256, cyl_tab_cage_hide_cage=True)

    def build(self):
        return self.assembly_node().composite('assembly').at('base', rh=1)


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)
   
if __name__ == '__main__':
    ad.anchorscad_main(False)

    
    