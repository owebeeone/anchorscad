'''
Created on 6 Jan 2022

@author: gianni
'''

import numpy as np
import ParametricSolid.core as core
from ParametricSolid.datatree import datatree, Node
import ParametricSolid.extrude as extrude
import ParametricSolid.linear as l

EPSILON=1.0e-3

@core.shape('anchorscad.models.components.buttons.ButtonWings')
@datatree
class ButtonWings(core.CompositeShape):
    '''
    <description>
    '''
    button_r: float=17.4 / 2
    button_h: float=5.7
    wing_r_inner_size: float=1.6
    wing_r_outer_size: float=1
    wing_h: float=3
    wing_count: int=5
    wing_angle: float=20
    
    extruder: Node=core.ShapeNode(extrude.RotateExtrude, {})
    
    wings_cage_shape: Node=core.ShapeNode(core.Cylinder, {'r': 'button_r', 'h': 'button_h'})
    winge_cageof_node: Node=Node(core.cageof, prefix='wings_cage_')
    fn=128
    
    EXAMPLE_SHAPE_ARGS=core.args(wings_cage_as_cage=False)
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        
        start = (self.button_r - self.wing_r_inner_size, 0)
        
        path = (extrude.PathBuilder()
            .move(start, direction=[0, 1])
            .stroke(self.wing_h, name='inner')
            .stroke(self.wing_r_inner_size, xform=l.ROTZ_270, name='top_lhs')
            .stroke(self.wing_r_outer_size, name='top_rhs')
            .stroke(self.wing_h, xform=l.ROTZ_270, name='outer')
            .stroke(self.wing_r_outer_size, xform=l.ROTZ_270, name='base_rhs')
            .line(start, 'base_lhs')
            .build()
            )
        maker = self.winge_cageof_node().at('base', post=l.ROTX_180)
        
        shape = self.extruder(path, degrees=self.wing_angle)
        
        angle_remaining = 360 - self.wing_count * self.wing_angle
        assert angle_remaining >= 0, 'Too many wings, they will overlap.'
        
        rot_angle_offset = - self.wing_angle / 2
        angle_per_wing = self.wing_angle + angle_remaining / self.wing_count
        for i in range(self.wing_count):
            maker.add_at(shape.solid(('wing', i)).at(),
                         post=l.rotZ(rot_angle_offset + i * angle_per_wing))
        self.maker = maker


@core.shape('anchorscad.models.components.buttons.ButtonCap')
@datatree
class ButtonCap(core.CompositeShape):
    '''
    <description>
    '''
    button_r: float=17.4 / 2
    button_h: float=5.7
    shaft_diameter: float=3.09
    shaft_taper: tuple=(0.3, 0.8)
    shaft_height: float=4.5
    edge_height: float=4.5
    rim_radius: float=0.75
    bottom_flange: tuple=(0.3, 0.4)
    bc_cage_shape: Node=core.ShapeNode(core.Cylinder, {'r': 'button_r', 'h': 'button_h'})
    cageof_node: Node=Node(core.cageof, prefix='bc_cage_')
    spline1_meta_data: object=core.ModelAttributes().with_fn(15)
    spline2_meta_data: object=core.ModelAttributes().with_fn(5)
    extruder: Node=core.ShapeNode(extrude.RotateExtrude, {'degrees': 'ex_degrees'})
    with_wings: bool=True
    wings_node: Node=core.ShapeNode(ButtonWings)
    engrave_shape: core.Shape=None
    
    EXAMPLE_SHAPE_ARGS=core.args(fn=128, bc_cage_as_cage=False)
    EXAMPLE_ANCHORS=(core.surface_args('base'),
                     core.surface_args('top'),)
    
    def __post_init__(self):
        start_point = [self.shaft_diameter / 2.0 + self.shaft_taper[0], 0]
        end_taper_point = [self.shaft_diameter / 2.0, self.shaft_taper[1]]
    
        shaft_height = self.shaft_height
        end_shaft_point1 = [self.shaft_diameter / 2.0, shaft_height]
        end_shaft_point2 = [0, shaft_height]
    
        top_point = [0, self.button_h]
    
        top_spline_points = [
            [self.button_r / 2, self.button_h],
            [self.button_r / 2, self.button_h],
            [self.button_r - self.rim_radius / 2, self.edge_height]]
    
        cp1 = np.array(top_spline_points[1])
        ep1 = np.array(top_spline_points[2])
        dir_vec = ep1 - cp1
        direction = dir_vec / np.linalg.norm(dir_vec)
        
        top_spline_to_rim_spline_tangent = [
            direction * self.rim_radius / 2 + ep1,
            [self.button_r, self.edge_height - self.rim_radius / 2],
            [self.button_r, self.edge_height - self.rim_radius]]
        
        rim_bottom_edge = [self.button_r, self.bottom_flange[1]]
        rim_bottom = [self.button_r - self.bottom_flange[0], 0]
        
        path = (extrude.PathBuilder()
            .move(start_point)
            .line(end_taper_point, 'shaft_taper')
            .line(end_shaft_point1, 'shaft_side')
            .line(end_shaft_point2, 'shaft_top')
            .line(top_point, 'centre_line')
            .spline(top_spline_points,
                          name='top_part1',
                          metadata=self.spline1_meta_data)
            .spline(top_spline_to_rim_spline_tangent,
                          name='top_part2',
                          metadata=self.spline2_meta_data)
            .line(rim_bottom_edge, 'outer')
            .line(rim_bottom, 'outer_to_base')
            .line(start_point, 'base')).build()
            
        shape = self.extruder(path)
        maker = self.cageof_node().at('base', post=l.ROTX_180)
        maker.add_at(shape.solid('button_cap')
                     .at('centre_line', 1.0, post=l.ROTX_270),
                     'top')
        
        wings_mode = (core.ModeShapeFrame.HOLE
                      if self.with_wings else
                      core.ModeShapeFrame.CAGE)
        wings_shape = self.wings_node()
        maker.add_at(wings_shape.named_shape('cap_wings', wings_mode).at('base'),
                     'base', post=l.tranZ(EPSILON))
        
        self.maker = maker

@core.shape('anchorscad.models.components.buttons.EngravedButtonCap')
@datatree
class EngravedButtonCap(core.CompositeShape):
    '''
    <description>
    '''
    button_node: Node=core.ShapeNode(ButtonCap)
    engrave_h: float=0.4
    engrave_shape: core.shape=None
    engrave_shape_anchor: core.AnchorArgs=core.surface_args()
    wing_count: int=2

    EXAMPLE_SHAPE_ARGS=core.args(
        engrave_shape=core.Text('⚓', 
                                size=14,
                                depth=10, 
                                halign='center', 
                                valign='center',
                                font="Segoe UI Symbol:style=Bold"),
        engrave_shape_anchor=core.surface_args(pre=l.scale([1., 1, 1])),
        fn=64)
    EXAMPLE_ANCHORS=()

    def __post_init__(self):

        outer_maker = (self.button_node().solid('outer_cap')
                                        #.transparent(True)
                                        .at())
        
        outer_maker.add_at(self.engrave_shape.hole('engraving')
                           .at(post=self.engrave_shape_anchor.apply(outer_maker)),
                           'top')
        
        maker = outer_maker.solid('outer_engraved').at()
        
        maker.add_at(self.button_node(
                        button_h=self.button_h - self.engrave_h,
                        edge_height=self.edge_height - self.engrave_h)
                     .solid('inner_cap')
                     .colour((1, 0, 0, 1))
                     .at('base'),
                     'base')

        self.maker = maker


if __name__ == '__main__':
    core.anchorscad_main(False)
