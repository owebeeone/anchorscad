'''
Created on 9 Jan 2022

@author: gianni
'''


from anchorscad import args, anchor, shape, surface_args, datatree, CompositeShape, \
    Node, EMPTY_ATTRS, ShapeNode, CageOfNode, Cylinder, ModeShapeFrame, anchorscad_main, \
    RotateExtrude, Path, PathBuilder, ROTX_90, ROTX_180, ROTY_180, ROTZ_90, ROTZ_180, \
    tranZ, ModuleDefault, Maker, to_degrees, dtfield, Shape
import anchorscad as ad

import anchorscad_models.components.switches.tactile_tl1105 as tactile_switches
import anchorscad_models.components.buttons.button_cap as button_cap

EPSILON=1.0e-3

@shape
@datatree
class ButtonBody(CompositeShape):
    '''
    Substrate of a button housing. This can make a fat switch from a
    small tactile switch but retaining the operating ease of the tactile switch.
    
    This is designed as a press fit onto the shaft of a 10-11mm tactile switch.
    The button cap and housing will limit travel and hence the operating forces
    are limited resulting in limited forces on the tactile switch regardless of
    the applied force on the button cap.
    '''
    bottom_plate_height: float=3
    top_plate_height: float=3
    inner_rim_height: float=3
    inner_rim_r: float=15 / 2
    outer_rim_height: float=4
    outer_rim_r: float=17.7 / 2
    outer_r: float=22.5 / 2
    inside_rim_top_r: float=1
    ouside_rim_top_r: float=2
    path: Path=None
    extents: tuple=None
    
    metadata: object=EMPTY_ATTRS.with_fn(8)
    cage_shape_node: Node=ShapeNode(Cylinder, {})
    angle: float=360
    extrude_node: Node=ShapeNode(RotateExtrude, 'angle')
    cage_node: Node=CageOfNode()
    plate_cage_node: Node=CageOfNode(prefix='plate_cage_')
    rim_cage_node: Node=CageOfNode(prefix='rim_cage_')
    
    WINGS_PRESERVE_SET={'button_r', 'button_h', 'wing_count'}
    
    with_wings: bool=True
    
    cap_node: Node=dtfield(ShapeNode(button_cap.ButtonCap), init=False)
    
    gap_size: float=0.5
    inner_size:float=dtfield(self_default=lambda s: s.button_r - s.inner_rim_r)
    wing_r_inner_size:float = dtfield(self_default=lambda s: s.inner_size + s.gap_size)
    cap_wing_r_inner_size:float = dtfield(self_default=lambda s: s.inner_size)
    cap_wing_h:float = dtfield(self_default=lambda s: s.wing_h - s.gap_size)
    cap_wing_angle:float = dtfield(self_default=lambda s: 
                                   s.wing_angle - to_degrees(2 * s.gap_size / s.button_r))
    
    cap_shape: Shape=dtfield(
        self_default=lambda s: s.cap_node(), init=False)
        
    body_wing_node: Node=ShapeNode(button_cap.ButtonWings, 
            preserve=WINGS_PRESERVE_SET,
            prefix='cap_')
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=args(hide_cage=True,
                                plate_cage_hide_cage=False, 
                                rim_cage_hide_cage=False,
                                angle=270)
    EXAMPLE_ANCHORS=(surface_args('base', scale_anchor=0.5),
                     surface_args('plate', scale_anchor=0.5),)
    
    def build(self) -> Maker:
        
        outside_radius = self.outer_r
        height = (self.top_plate_height
            + self.inner_rim_height
            + self.outer_rim_height)
        
        start_point = [0, -self.bottom_plate_height]
        rim_outer = [self.outer_rim_r,
                     self.top_plate_height + self.inner_rim_height]

        rim_spline1 = [
            [rim_outer[0], height - self.inside_rim_top_r / 3.0],
            [rim_outer[0] + self.inside_rim_top_r / 3.0, height],
            [rim_outer[0] + self.inside_rim_top_r, height]]
        
        rim_spline2 = [
            [rim_outer[0] + self.inside_rim_top_r + self.ouside_rim_top_r / 2.0, 
             height],
            [outside_radius, height - self.ouside_rim_top_r / 2.0],
            [outside_radius, height - self.ouside_rim_top_r]]
        
        path = (PathBuilder()
                .move(start_point)
                .line([0, self.top_plate_height], 'plate_centre')
                .line([self.inner_rim_r, self.top_plate_height], 'plate_outer')
                .line([self.inner_rim_r,
                     self.top_plate_height + self.inner_rim_height], 'rim_inner')
                .line(rim_outer, 'rim_outer')
                .spline(rim_spline1, metadata=self.metadata, name='rim1')
                .spline(rim_spline2, metadata=self.metadata, name='rim2')
                .line([outside_radius, - self.bottom_plate_height], 'bottom_outer')
                .line(start_point, 'axis')
                .build())
        self.path = path
        self.extents = path.extents()
        extents = path.extents()
        
        cage_shape = self.cage_shape_node(h=extents[1][1] - extents[0][1], 
                                   r=extents[1][0] - extents[0][0])
        maker = self.cage_node(cage_shape).at('base', post=ROTX_180)
        
        cage_plate_shape = self.cage_shape_node(h=self.top_plate_height,
                                                r=self.inner_rim_r)
        maker.add_at(
            self.plate_cage_node(cage_plate_shape, cage_name='plate_cage')
            .at('base'), 'base', h=self.bottom_plate_height)
        
        rim_plate_shape = self.cage_shape_node(h=self.top_plate_height,
                                                r=self.outer_rim_r)
        maker.add_at(
            self.rim_cage_node(rim_plate_shape, cage_name='rim_plate_cage')
            .at('base'), 'plate_cage', 'base', rh=1)

        shape = self.extrude_node(path)
        maker.add_at(shape.solid('body').at('plate_centre'),
                     'base', post=ROTY_180 * ROTX_90)
        
        wings_mode = (ModeShapeFrame.SOLID
                      if self.with_wings else
                      ModeShapeFrame.CAGE)
        wings_shape = self.body_wing_node()
        maker.add_at(wings_shape.named_shape('body_wings', wings_mode).at('base'),
                     'rim_plate_cage', 'base', rh=1, post=ROTZ_180 * tranZ(-EPSILON))
        return maker

    @anchor('Plate top.')
    def plate(self, *args, **kwds):
        return self.maker.at('plate_cage', 'top', *args, **kwds)


@shape
@datatree
class ButtonForTactileSwitch(CompositeShape):
    '''
    Button housing for tactile switches.
    '''
    
    leads_hide_cages: bool=True
    switch_type: str=None
    tl1105_node: Node=ShapeNode(tactile_switches.TactileSwitchTL1105, 
                                     {'leada_node': 'tl1105_leada_node'})
    tl59_node: Node=ShapeNode(tactile_switches.TactileSwitchTL59, 
                                     {'leada_node': 'tl59_leada_node'})
    outline_node: Node=ShapeNode(tactile_switches.TactileSwitchOutline)
    body_node: Node=ShapeNode(
            ButtonBody, 
            prefix='body_', 
            preserve=ButtonBody.WINGS_PRESERVE_SET.union(
                {'cap_wing_r_inner_size',
                 'cap_wing_r_outer_size',
                 'cap_wing_h',
                 'cap_wing_angle'}))
    
    body_shape: Shape=dtfield(
        self_default=lambda s: s.body_node(), init=False)
    
    make_cap: bool=False
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=args(switch_type='TL59', wing_count=4, body_gap_size=0.5)
    EXAMPLE_ANCHORS=tuple()
    EXAMPLES_EXTENDED={
        'example2_cap': ad.ExampleParams(
            shape_args=ad.apply_args(EXAMPLE_SHAPE_ARGS, make_cap=True),
            anchors=())
        }
    
    def build(self) -> Maker:
        body = self.body_shape
        
        if self.make_cap:
            maker = body.cap_shape.solid('cap').at()
            return maker
        
        maker = body.solid('body').at()
        
        switch_node = self.select_switch()
        
        switch_shape = self.outline_node(switch_shape=switch_node())
        
        maker.add_at(switch_shape.hole('switch_hole').at('switch_top'),
                     'plate_cage', 'top', post=tranZ(EPSILON))
        
        return maker

    def select_switch(self):
        if self.switch_type is None:
            return self.tl1105_node
        
        if self.switch_type == 'TL59':
            return self.tl59_node
        
        if self.switch_type == 'TL1105':
            return self.tl1105_node
        
        assert False, f'Failed to find switch_type {self.switch_type!r}.'


@shape
@datatree
class ButtonAssemblyTest(CompositeShape):
    '''
    A test assembly of a button and a tactile switch.
    '''
    
    base_node: Node=ShapeNode(ButtonForTactileSwitch)
    wing_count: int=4
    wing_angle: float=20

    EXAMPLE_SHAPE_ARGS=args(switch_type='TL1105',
                            body_hide_cage=True,
                            body_plate_cage_hide_cage=True, 
                            body_angle=270, 
                            body_ex_angle=270,
                            fn=64)
    EXAMPLE_ANCHORS=tuple()
    
    def build(self) -> Maker:

        shape = self.base_node()
        
        maker = shape.solid('base').at(post=ROTZ_90)

        switch = shape.select_switch()(leads_hide_cages=False)
        
        maker.add_at(switch.solid('switch').colour([1, 0.3, 0.1, 1]).at('switch_base'),
                     'switch_hole', 'switch_base')
        
        cap_shape = shape.body_shape.cap_shape
        
        maker.add_at(cap_shape.solid('cap').colour([1, 0.3, 0.8, 1]).at('base'),
                     'rim_plate_cage', 'base', rh=1, post=ROTZ_180 * tranZ(-0.))
        
        return maker


MAIN_DEFAULT=ModuleDefault(all=True)
if __name__ == '__main__':
    anchorscad_main(False)
