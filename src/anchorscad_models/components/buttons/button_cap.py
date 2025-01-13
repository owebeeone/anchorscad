'''
Created on 6 Jan 2022

@author: gianni
'''

import numpy as np
import anchorscad as ad

EPSILON=1.0e-3

@ad.shape
@ad.datatree
class ButtonWings(ad.CompositeShape):
    '''
    Guides (holes or solids) for keeping the button from rotating.
    '''
    button_r: float=17.4 / 2
    button_h: float=5.7
    wing_r_inner_size: float=1.6
    wing_r_outer_size: float=1
    wing_h: float=3
    wing_count: int=5
    wing_angle: float=20
    
    extruder: ad.Node=ad.ShapeNode(ad.RotateExtrude, {})
    
    wings_cage_shape: ad.Node=ad.ShapeNode(
        ad.Cylinder, {'r': 'button_r', 'h': 'button_h'})
    winge_cageof_node: ad.Node=ad.Node(ad.cageof, prefix='wings_cage_')
    fn=128
    
    EXAMPLE_SHAPE_ARGS=ad.args(wings_cage_hide_cage=False,
                               wing_angle=10,
                               wing_r_inner_size=2,
                               wing_count=4)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        
        start = (self.button_r - self.wing_r_inner_size, 0)
        
        path = (ad.PathBuilder()
            .move(start, direction=[0, 1])
            .stroke(self.wing_h, name='inner')
            .stroke(self.wing_r_inner_size, xform=ad.ROTZ_270, name='top_lhs')
            .stroke(self.wing_r_outer_size, name='top_rhs')
            .stroke(self.wing_h, xform=ad.ROTZ_270, name='outer')
            .stroke(self.wing_r_outer_size, xform=ad.ROTZ_270, name='base_rhs')
            .line(start, 'base_lhs')
            .build()
            )
        maker = self.winge_cageof_node().at('base', post=ad.ROTX_180)
        
        shape = self.extruder(path, angle=self.wing_angle)
        
        angle_remaining = 360 - self.wing_count * self.wing_angle
        assert angle_remaining >= 0, 'Too many wings, they will overlap.'
        
        rot_angle_offset = - self.wing_angle / 2
        if self.wing_count> 0:
            angle_per_wing = self.wing_angle + angle_remaining / self.wing_count
            for i in range(self.wing_count):
                maker.add_at(shape.solid(('wing', i)).at(),
                             post=ad.rotZ(rot_angle_offset + i * angle_per_wing))
        return maker


@ad.shape
@ad.datatree
class ButtonCap(ad.CompositeShape):
    '''
    A button cap with a shaft hole and optional engraving.
    '''
    button_r: float=17.4 / 2
    button_h: float=5.7
    shaft_diameter: float=3.09
    shaft_taper: tuple=(0.3, 0.8)
    shaft_height: float=4.5
    edge_height: float=4.5
    rim_radius: float=0.75
    bottom_flange: tuple=(0.3, 0.4)
    bc_cage_shape: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'button_r', 'h': 'button_h'})
    cageof_node: ad.Node=ad.Node(ad.cageof, prefix='bc_cage_')
    spline1_meta_data: object=ad.ModelAttributes().with_fn(15)
    spline2_meta_data: object=ad.ModelAttributes().with_fn(5)
    extruder: ad.Node=ad.ShapeNode(ad.RotateExtrude, {'angle': 'ex_angle'})
    with_wings: bool=True
    wings_node: ad.Node=ad.ShapeNode(ButtonWings)
    engrave_shape: ad.Shape=None
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128, bc_cage_hide_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('base'),
                     ad.surface_args('top'),)
    
    def build(self) -> ad.Maker:
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
        
        path = (ad.PathBuilder()
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
        maker = self.cageof_node().at('base', post=ad.ROTX_180)
        maker.add_at(shape.solid('button_cap')
                     .at('centre_line', 1.0, post=ad.ROTX_270),
                     'top')
        
        wings_mode = (ad.ModeShapeFrame.HOLE
                      if self.with_wings else
                      ad.ModeShapeFrame.CAGE)
        wings_shape = self.wings_node()
        maker.add_at(wings_shape.named_shape('cap_wings', wings_mode).at('base'),
                     'base', post=ad.tranZ(EPSILON))
        
        return maker

@ad.shape
@ad.datatree
class EngravedButtonCap(ad.CompositeShape):
    '''
    An example button cap with an engraving.
    '''
    button_node: ad.Node=ad.ShapeNode(ButtonCap)
    engrave_h: float=0.4
    engrave_shape: ad.shape=None
    engrave_shape_anchor: ad.AnchorArgs=ad.surface_args()
    wing_count: int=4

    EXAMPLE_SHAPE_ARGS=ad.args(
        wing_count=4,
        engrave_shape=ad.Text('⚓', 
                                size=14,
                                depth=10, 
                                halign='center', 
                                valign='center',
                                font="Segoe UI Symbol:style=Bold"),
        engrave_shape_anchor=ad.surface_args(pre=ad.scale([1., 1, 1]), post=ad.tranZ(3)),
        fn=64)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:

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

        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
